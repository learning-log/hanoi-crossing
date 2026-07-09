"""Tests for formatting and replay I/O helpers."""

import json
from pathlib import Path

import pytest

from hanoi_crossing.actions import Action, ActionKind
from hanoi_crossing.engine import HanoiCrossingEngine
from hanoi_crossing.formatting import (
    action_to_dict,
    format_board,
    format_observation,
    format_result,
    format_trace,
    format_traces,
    load_replay,
    observation_to_dict,
    parse_replay_text,
    result_to_dict,
    state_to_dict,
    trace_to_dict,
)
from hanoi_crossing.models import Observation
from hanoi_crossing.runner import EpisodeRunner


def test_format_board():
    engine = HanoiCrossingEngine(1)
    text = format_board(engine.state)
    assert "Board:" in text
    assert "1a:" in text
    assert "hands: A=None, B=None" in text


def test_format_observation():
    obs = Observation(player="A", poles={"1": (1,), "2": (), "3": ()}, hand=None)
    assert "hand=empty" in format_observation(obs)

    holding = Observation(player="B", poles={"1": (2,), "2": (), "3": ()}, hand=2)
    assert "hand=2" in format_observation(holding)


def test_state_and_observation_to_dict():
    engine = HanoiCrossingEngine(1)
    obs = engine.observe("A")
    state = state_to_dict(engine.state)
    assert state["poles"]["1a"] == [1]
    assert observation_to_dict(obs)["hand"] is None
    assert action_to_dict(Action(ActionKind.LIFT, "1")) == {"kind": "lift", "pole": "1"}


def test_format_trace_and_traces():
    engine = HanoiCrossingEngine(1, turn_order=["A"])
    runner = EpisodeRunner(engine)
    runner.run_turn("A", Action(ActionKind.LIFT, "1"))
    trace = runner.traces[0]

    text = format_trace(trace)
    assert "A -> lift 1" in text
    assert "Trace: (empty)" == format_traces([])

    traces_text = format_traces(runner.traces)
    assert traces_text.startswith("Trace:")
    assert trace_to_dict(trace)["valid"] is True


def test_format_trace_invalid_shows_reason():
    engine = HanoiCrossingEngine(1, turn_order=["A"])
    runner = EpisodeRunner(engine)
    runner.run_turn("A", Action(ActionKind.PLACE, "3"))
    text = format_trace(runner.traces[0])
    assert "INVALID" in text
    assert "illegal action" in text


def test_result_to_dict_and_format_result():
    engine = HanoiCrossingEngine(1, turn_order=["A", "B", "A"])
    runner = EpisodeRunner(engine)
    runner.run_scripted(
        [
            ("A", Action(ActionKind.LIFT, "1")),
            ("B", Action(ActionKind.LIFT, "1")),
            ("A", Action(ActionKind.PLACE, "3")),
        ],
        strict=True,
    )

    payload = result_to_dict(engine, traces=runner.traces)
    assert payload["winner"] == "A"
    assert len(payload["trace"]) == 3

    text = format_result(engine, traces=runner.traces)
    assert "Winner: Player A" in text
    assert "Trace:" in text


def test_format_result_in_progress():
    engine = HanoiCrossingEngine(1, turn_order=["A", "B"])
    text = format_result(engine)
    assert "Game in progress." in text


def test_format_result_done_without_winner():
    engine = HanoiCrossingEngine(1)
    engine._done = True
    text = format_result(engine)
    assert "Game over (no winner recorded)." in text


def test_parse_replay_text_errors():
    with pytest.raises(ValueError, match="unrecognized replay line"):
        parse_replay_text("n 1\nnot a valid line\n")

    with pytest.raises(ValueError, match="bad move line"):
        parse_replay_text("n 1\nmove only\n")

    with pytest.raises(ValueError, match="must include 'n <disks>'"):
        parse_replay_text("turn A\n")


def test_load_replay_txt_and_json(tmp_path: Path):
    txt = tmp_path / "game.txt"
    txt.write_text("n 1\nturn A\nmove A skip\n")
    n, turn_order, moves = load_replay(txt)
    assert n == 1
    assert moves == [("A", Action(ActionKind.SKIP))]

    js = tmp_path / "game.json"
    js.write_text(json.dumps({"n": 1, "turn_order": ["A"], "moves": [{"player": "A", "action": "skip"}]}))
    n2, turn_order2, moves2 = load_replay(js)
    assert n2 == 1
    assert moves2 == [("A", Action(ActionKind.SKIP))]
