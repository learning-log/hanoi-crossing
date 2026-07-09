"""Tests for agents, runner, replay validation, and traces."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

from hanoi_crossing.actions import Action, ActionKind
from hanoi_crossing.agents import RandomAgent, ScriptedAgent
from hanoi_crossing.engine import HanoiCrossingEngine
from hanoi_crossing.formatting import load_replay, parse_replay_json
from hanoi_crossing.runner import EpisodeRunner, ReplayValidationError, validate_replay


def test_validate_replay_accepts_matching_moves():
    validate_replay(["A", "B", "A"], [("A", Action(ActionKind.SKIP)), ("B", Action(ActionKind.SKIP)), ("A", Action(ActionKind.SKIP))])


def test_validate_replay_rejects_player_mismatch():
    with pytest.raises(ReplayValidationError, match="move 2"):
        validate_replay(["A", "B"], [("A", Action(ActionKind.SKIP)), ("A", Action(ActionKind.SKIP))])


def test_validate_replay_rejects_extra_moves():
    with pytest.raises(ReplayValidationError, match="more move"):
        validate_replay(["A"], [("A", Action(ActionKind.SKIP)), ("B", Action(ActionKind.SKIP))])


def test_validate_replay_rejects_fewer_moves():
    with pytest.raises(ReplayValidationError, match="fewer move"):
        validate_replay(["A", "B"], [("A", Action(ActionKind.SKIP))])


def test_episode_runner_collects_trace():
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

    assert len(runner.traces) == 3
    assert runner.traces[0].valid
    assert runner.traces[0].acting_player == "A"
    assert runner.traces[0].action == Action(ActionKind.LIFT, "1")
    assert runner.traces[0].legal_actions
    assert runner.traces[-1].winner == "A"


def test_step_result_includes_decision_context():
    engine = HanoiCrossingEngine(1, turn_order=["A"])
    result = engine.step("A", Action(ActionKind.LIFT, "1"))

    assert result.valid
    assert result.acting_player == "A"
    assert result.action == Action(ActionKind.LIFT, "1")
    assert result.observation is not None
    assert Action(ActionKind.LIFT, "1") in result.legal_actions
    assert result.turn_index == 0


def test_random_agent_via_runner():
    engine = HanoiCrossingEngine(1, turn_order=["A", "B", "A"])
    runner = EpisodeRunner(engine)
    runner.run_agent(RandomAgent(__import__("random").Random(0)))

    assert len(runner.traces) == 3
    assert all(trace.legal_actions for trace in runner.traces)


def test_agent_act_receives_observation_and_legal_actions():
    engine = HanoiCrossingEngine(1, turn_order=["A"])
    observation = engine.observe("A")
    legal_actions = engine.legal_actions("A")
    action = RandomAgent(__import__("random").Random(0)).act(observation, legal_actions)
    assert action in legal_actions


def test_scripted_agent_via_runner():
    engine = HanoiCrossingEngine(1, turn_order=["A", "A", "B"])
    runner = EpisodeRunner(engine)
    agent = ScriptedAgent(
        [
            Action(ActionKind.LIFT, "1"),
            Action(ActionKind.PLACE, "2"),
            Action(ActionKind.LIFT, "2"),
        ]
    )
    runner.run_agent(agent)

    assert engine.state.hands["B"] == 1


def test_game_stops_after_winner():
    engine = HanoiCrossingEngine(1, turn_order=["A", "B", "A", "B"])
    runner = EpisodeRunner(engine)
    runner.run_scripted(
        [
            ("A", Action(ActionKind.LIFT, "1")),
            ("B", Action(ActionKind.LIFT, "1")),
            ("A", Action(ActionKind.PLACE, "3")),
            ("B", Action(ActionKind.SKIP)),
        ],
        strict=True,
    )

    assert engine.winner == "A"
    assert len(runner.traces) == 3


def test_run_scripted_stops_after_winner():
    engine = HanoiCrossingEngine(1, turn_order=["A", "B", "A", "A"])
    winner = EpisodeRunner(engine).run_scripted(
        [
            ("A", Action(ActionKind.LIFT, "1")),
            ("B", Action(ActionKind.LIFT, "1")),
            ("A", Action(ActionKind.PLACE, "3")),
            ("A", Action(ActionKind.SKIP)),
        ],
    )

    assert winner == "A"
    assert engine.turn_index == 3


def test_step_after_game_over_is_rejected():
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
    result = engine.step("A", Action(ActionKind.SKIP))

    assert not result.valid
    assert result.reason == "game already finished"


def test_both_players_can_hold_disks():
    engine = HanoiCrossingEngine(1, turn_order=["A", "B"])
    runner = EpisodeRunner(engine)
    runner.run_scripted(
        [
            ("A", Action(ActionKind.LIFT, "1")),
            ("B", Action(ActionKind.LIFT, "1")),
        ],
        strict=True,
    )

    assert engine.state.hands["A"] == 1
    assert engine.state.hands["B"] == 2


def test_json_replay_round_trip(tmp_path):
    data = {
        "n": 1,
        "turn_order": ["A", "B", "A"],
        "moves": [
            {"player": "A", "action": "lift 1"},
            {"player": "B", "action": "lift 1"},
            {"player": "A", "action": "place 3"},
        ],
    }
    path = tmp_path / "game.json"
    path.write_text(json.dumps(data))
    n, turn_order, moves = load_replay(path)
    engine = HanoiCrossingEngine(n, turn_order=turn_order)
    winner = EpisodeRunner(engine).run_scripted(moves, strict=True)
    assert winner == "A"


def test_parse_replay_json_helper():
    n, turn_order, moves = parse_replay_json(
        {
            "n": 2,
            "turn_order": ["A", "B"],
            "moves": [{"player": "A", "action": "skip"}],
        }
    )
    assert n == 2
    assert turn_order == ["A", "B"]
    assert moves == [("A", Action(ActionKind.SKIP))]


def test_replay_cli_with_trace_flag():
    result = subprocess.run(
        [sys.executable, "-m", "hanoi_crossing.cli.replay", "examples/n1_win.txt", "--trace"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Trace:" in result.stdout
    assert "Winner: Player A" in result.stdout


def test_validate_replay_empty_turn_order_is_noop():
    validate_replay([], [("A", Action(ActionKind.SKIP))])


def test_run_agent_max_steps():
    engine = HanoiCrossingEngine(1, turn_order=["A", "B", "A", "B"])
    runner = EpisodeRunner(engine)
    runner.run_agent(RandomAgent(__import__("random").Random(0)), max_steps=1)
    assert len(runner.traces) == 1
    assert not engine.done


def test_run_scripted_non_strict_allows_mismatch():
    engine = HanoiCrossingEngine(1, turn_order=["A"])
    runner = EpisodeRunner(engine)
    runner.run_scripted([("B", Action(ActionKind.SKIP))], strict=False)
    assert len(runner.traces) == 1
    assert not runner.traces[0].valid


def test_reset_traces():
    engine = HanoiCrossingEngine(1, turn_order=["A"])
    runner = EpisodeRunner(engine)
    runner.run_turn("A", Action(ActionKind.SKIP))
    runner.reset_traces()
    assert runner.traces == []


def test_scripted_agent_exhausted_actions_falls_back_to_legal():
    engine = HanoiCrossingEngine(1, turn_order=["A", "A"])
    agent = ScriptedAgent([Action(ActionKind.LIFT, "1")])
    EpisodeRunner(engine).run_agent(agent)
    assert engine.state.hands["A"] == 1


def test_replay_cli_rejects_mismatched_replay(tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text("n 1\nturn A B\nmove B skip\nmove A skip\n")
    result = subprocess.run(
        [sys.executable, "-m", "hanoi_crossing.cli.replay", str(bad)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "move 1" in result.stderr
