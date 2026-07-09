"""Tests for the Hanoi Crossing engine and frontends."""

from __future__ import annotations

from pathlib import Path

import pytest

from hanoi_crossing import Action, ActionKind, Game, Player, RandomAgent
from hanoi_crossing.cli import run_random, run_replay, run_replay_file
from hanoi_crossing.engine import parse_action
from hanoi_crossing.runner import EpisodeRunner, ReplayValidationError, validate_replay


EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


class TestInitialState:
  def test_stacks_for_n3(self) -> None:
    game = Game(3, ["A", "B"])
    assert game.poles["1a"] == [5, 3, 1]
    assert game.poles["1b"] == [6, 4, 2]
    assert game.poles["2"] == []


class TestRules:
  def test_illegal_lift_wastes_turn(self) -> None:
    game = Game(1, ["A", "A"])
    game.step(Player.A, Action(ActionKind.LIFT, 1))
    result = game.step(Player.A, Action(ActionKind.LIFT, 1))
    assert not result.legal
    assert game.hands[Player.A] == 1
    assert game.turn_index == 2

  def test_illegal_place_wastes_turn(self) -> None:
    game = Game(2, ["A", "A", "A", "A"])
    game.step(Player.A, Action(ActionKind.LIFT, 1))
    game.step(Player.A, Action(ActionKind.PLACE, 2))
    game.step(Player.A, Action(ActionKind.LIFT, 1))
    result = game.step(Player.A, Action(ActionKind.PLACE, 2))
    assert not result.legal
    assert game.hands[Player.A] == 3
    assert game.poles["2"] == [1]

  def test_shared_pole_visible_to_both(self) -> None:
    game = Game(1, ["A", "B", "A"])
    game.step(Player.A, Action(ActionKind.LIFT, 1))
    game.step(Player.B, Action(ActionKind.SKIP))
    game.step(Player.A, Action(ActionKind.PLACE, 2))
    assert game.poles["2"] == [1]
    obs_b = game.observe(Player.B)
    assert obs_b["poles"][2] == [1]

  def test_either_player_can_lift_from_shared(self) -> None:
    game = Game(1, ["A", "B", "A", "B"])
    game.step(Player.A, Action(ActionKind.LIFT, 1))
    game.step(Player.B, Action(ActionKind.SKIP))
    game.step(Player.A, Action(ActionKind.PLACE, 2))
    game.step(Player.B, Action(ActionKind.LIFT, 2))
    assert game.hands[Player.B] == 1
    assert game.poles["2"] == []

  def test_skip_is_always_legal(self) -> None:
    game = Game(1, ["A"])
    assert Action(ActionKind.SKIP) in game.legal_actions()


class TestWinCondition:
  def test_example_from_brief(self) -> None:
    moves = [
      Action(ActionKind.LIFT, 1),
      Action(ActionKind.LIFT, 1),
      Action(ActionKind.PLACE, 3),
    ]
    game = run_replay(1, [Player.A, Player.B, Player.A], moves)
    assert game.winner == Player.A
    assert game.hands[Player.A] is None
    assert game.poles["1a"] == []
    assert game.poles["2"] == []
    assert game.poles["3a"] == [1]

  def test_no_win_with_empty_pole3(self) -> None:
    game = Game(1, ["A"])
    game.step(Player.A, Action(ActionKind.LIFT, 1))
    assert game.winner is None


class TestReplayCLI:
  def test_json_replay(self) -> None:
    game = run_replay_file(EXAMPLES / "n1_win.json")
    assert game.winner == Player.A

  def test_text_replay(self) -> None:
    game = run_replay_file(EXAMPLES / "n1_win.txt")
    assert game.winner == Player.A


class TestRandomPlay:
  def test_runs_without_error(self) -> None:
    game = run_random(2, max_turns=50, seed=0)
    assert game.turn_index > 0

  def test_random_agent_picks_legal_action(self) -> None:
    import random

    game = Game(1, ["A"])
    agent = RandomAgent(random.Random(0))
    action = agent.act(game, Player.A)
    assert action in game.legal_actions(Player.A)

  def test_uses_only_legal_moves(self) -> None:
    game = Game(2, ["A"] * 20)
    for _ in range(20):
      player = game.expected_player
      assert player is not None
      action = game.legal_actions(player)[0]
      assert game.is_legal(action, player)
      game.step(player, action)


class TestAgentsAndRunner:
  def test_episode_runner_collects_traces(self) -> None:
    game = Game(1, ["A", "B"])
    runner = EpisodeRunner(game)
    runner.run_scripted(
      [
        (Player.A, Action(ActionKind.LIFT, 1)),
        (Player.B, Action(ActionKind.SKIP)),
      ]
    )
    assert len(runner.traces) == 2
    assert runner.traces[0].acting_player == Player.A
    assert runner.traces[0].valid

  def test_episode_runner_with_scripted_moves(self) -> None:
    moves = [
      (Player.A, Action(ActionKind.LIFT, 1)),
      (Player.B, Action(ActionKind.LIFT, 1)),
      (Player.A, Action(ActionKind.PLACE, 3)),
    ]
    game = Game(1, [Player.A, Player.B, Player.A])
    winner = EpisodeRunner(game).run_scripted(moves, strict=True)
    assert winner == Player.A

  def test_validate_replay_rejects_mismatch(self) -> None:
    moves = [(Player.B, Action(ActionKind.SKIP))]
    with pytest.raises(ReplayValidationError):
      validate_replay([Player.A], moves)


class TestParseAction:
  def test_skip(self) -> None:
    assert parse_action("skip").kind == ActionKind.SKIP

  def test_lift(self) -> None:
    action = parse_action("lift", 2)
    assert action == Action(ActionKind.LIFT, 2)
