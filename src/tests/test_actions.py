"""Tests for action parsing and formatting."""

import pytest

from hanoi_crossing.actions import Action, ActionKind, format_actions, parse_action, parse_player


def test_action_str():
    assert str(Action(ActionKind.SKIP)) == "skip"
    assert str(Action(ActionKind.LIFT, "1")) == "lift 1"
    assert str(Action(ActionKind.PLACE, "3")) == "place 3"


def test_parse_action_skip():
    assert parse_action("skip") == Action(ActionKind.SKIP)


def test_parse_action_lift_and_place():
    assert parse_action("lift 2") == Action(ActionKind.LIFT, "2")
    assert parse_action("PLACE 3") == Action(ActionKind.PLACE, "3")


@pytest.mark.parametrize(
    "line, match",
    [
        ("", "empty action line"),
        ("skip extra", "skip takes no arguments"),
        ("lift", "expected lift|place"),
        ("lift 4", "expected lift|place"),
        ("nope 1", "ActionKind"),
    ],
)
def test_parse_action_errors(line, match):
    with pytest.raises(ValueError, match=match):
        parse_action(line)


def test_parse_player():
    assert parse_player("a") == "A"
    assert parse_player(" B ") == "B"


def test_parse_player_invalid():
    with pytest.raises(ValueError, match="invalid player"):
        parse_player("C")


def test_format_actions():
    actions = [Action(ActionKind.SKIP), Action(ActionKind.LIFT, "1")]
    assert format_actions(actions) == ["skip", "lift 1"]
