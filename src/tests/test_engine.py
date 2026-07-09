"""Engine tests for Hanoi Crossing."""

import pytest

from hanoi_crossing.actions import Action, ActionKind
from hanoi_crossing.engine import HanoiCrossingEngine
from hanoi_crossing.formatting import load_replay, parse_replay_text
from hanoi_crossing.models import BoardState
from hanoi_crossing.runner import EpisodeRunner


def test_initial_state_n1():
    engine = HanoiCrossingEngine(1)
    obs_a = engine.observe("A")
    obs_b = engine.observe("B")

    assert obs_a.poles == {"1": (1,), "2": (), "3": ()}
    assert obs_a.hand is None
    assert obs_b.poles == {"1": (2,), "2": (), "3": ()}
    assert obs_b.hand is None


def test_initial_state_n3():
    engine = HanoiCrossingEngine(3)
    assert engine.observe("A").poles["1"] == (5, 3, 1)
    assert engine.observe("B").poles["1"] == (6, 4, 2)


def test_example_win_n1():
    engine = HanoiCrossingEngine(1, turn_order=["A", "B", "A"])
    winner = EpisodeRunner(engine).run_scripted(
        [
            ("A", Action(ActionKind.LIFT, "1")),
            ("B", Action(ActionKind.LIFT, "1")),
            ("A", Action(ActionKind.PLACE, "3")),
        ],
        strict=True,
    )

    assert winner == "A"
    assert engine.done
    assert engine.state.hands["A"] is None
    assert engine.state.poles["1a"] == []
    assert engine.state.poles["2"] == []
    assert engine.state.poles["3a"] == [1]


def test_illegal_place_wastes_turn():
    engine = HanoiCrossingEngine(1, turn_order=["A"])
    result = engine.step("A", Action(ActionKind.PLACE, "3"))

    assert not result.valid
    assert result.reason == "illegal action"
    assert engine.turn_index == 1
    assert engine.state.poles["1a"] == [1]


def test_lift_while_holding_is_illegal():
    engine = HanoiCrossingEngine(1, turn_order=["A", "A"])
    engine.step("A", Action(ActionKind.LIFT, "1"))
    result = engine.step("A", Action(ActionKind.LIFT, "2"))

    assert not result.valid
    assert engine.state.hands["A"] == 1


def test_shared_pole_visible_to_both_players():
    engine = HanoiCrossingEngine(1, turn_order=["A", "A"])
    engine.step("A", Action(ActionKind.LIFT, "1"))
    engine.step("A", Action(ActionKind.PLACE, "2"))

    assert engine.observe("A").poles["2"] == (1,)
    assert engine.observe("B").poles["2"] == (1,)


def test_b_can_lift_from_shared_pole():
    engine = HanoiCrossingEngine(1, turn_order=["A", "A", "B"])
    engine.step("A", Action(ActionKind.LIFT, "1"))
    engine.step("A", Action(ActionKind.PLACE, "2"))
    result = engine.step("B", Action(ActionKind.LIFT, "2"))

    assert result.valid
    assert engine.state.hands["B"] == 1
    assert engine.state.poles["2"] == []


def test_legal_actions_include_skip():
    engine = HanoiCrossingEngine(1)
    assert Action(ActionKind.SKIP) in engine.legal_actions("A")


def test_wrong_player_wastes_turn_but_does_not_mutate_board():
    engine = HanoiCrossingEngine(1, turn_order=["A"])
    before = engine.state

    result = engine.step("B", Action(ActionKind.SKIP))

    assert not result.valid
    assert result.reason == "expected player A, got B"
    assert engine.turn_index == 1
    assert engine.state.poles == before.poles
    assert engine.state.hands == before.hands
    assert not engine.done


def test_replay_parser():
    text = """
    n 2
    turn A B
    move A lift 1
    move B skip
    """
    n, turn_order, moves = parse_replay_text(text)
    assert n == 2
    assert turn_order == ["A", "B"]
    assert len(moves) == 2


def test_replay_file_example(tmp_path):
    replay = tmp_path / "game.txt"
    replay.write_text(
        "n 1\nturn A B A\nmove A lift 1\nmove B lift 1\nmove A place 3\n"
    )
    n, turn_order, moves = load_replay(replay)
    engine = HanoiCrossingEngine(n, turn_order=turn_order)
    assert EpisodeRunner(engine).run_scripted(moves, strict=True) == "A"


def test_place_on_pole3_requires_larger_top_disk():
    engine = HanoiCrossingEngine(2, turn_order=["A", "A", "A", "A"])
    engine.step("A", Action(ActionKind.LIFT, "1"))  # lift disk 1
    engine.step("A", Action(ActionKind.PLACE, "3"))  # place on empty 3a
    engine.step("A", Action(ActionKind.LIFT, "1"))  # lift disk 3
    result = engine.step("A", Action(ActionKind.PLACE, "3"))  # cannot place 3 on 1

    assert not result.valid
    assert engine.state.poles["3a"] == [1]


def test_engine_rejects_invalid_n():
    with pytest.raises(ValueError, match="n must be >= 1"):
        HanoiCrossingEngine(0)


def test_engine_run_stops_after_winner():
    engine = HanoiCrossingEngine(1, turn_order=["A", "B", "A", "A"])
    winner = engine.run(
        [
            ("A", Action(ActionKind.LIFT, "1")),
            ("B", Action(ActionKind.LIFT, "1")),
            ("A", Action(ActionKind.PLACE, "3")),
            ("A", Action(ActionKind.SKIP)),
        ]
    )
    assert winner == "A"
    assert engine.turn_index == 3


def test_opponent_win_detected_when_shared_pole_cleared():
    """A is already solved except shared pole 2; B clearing it ends the game."""
    state = BoardState(
        poles={"1a": [], "1b": [4, 2], "2": [2], "3a": [3, 1], "3b": []},
        hands={"A": None, "B": None},
    )
    engine = HanoiCrossingEngine(2, turn_order=["B"], state=state)
    result = engine.step("B", Action(ActionKind.LIFT, "2"))

    assert result.valid
    assert engine.winner == "A"
    assert engine.done


def test_simultaneous_win_tiebreak_credits_acting_player():
    state = BoardState(
        poles={"1a": [], "1b": [], "2": [], "3a": [1], "3b": [2]},
        hands={"A": None, "B": None},
    )
    engine = HanoiCrossingEngine(1, turn_order=["A"], state=state)
    engine.step("A", Action(ActionKind.SKIP))

    assert engine.winner == "A"
    assert engine.done
