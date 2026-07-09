"""Tests for the Hanoi Crossing engine and frontends."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hanoi_crossing import Action, ActionKind, Game, Player, RandomAgent, ScriptedAgent
from hanoi_crossing.cli import run_random, run_replay, run_replay_file
from hanoi_crossing.engine import parse_action
from hanoi_crossing.runner import EpisodeRunner


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
    game.step(Action(ActionKind.LIFT, 1))
    result = game.step(Action(ActionKind.LIFT, 1))  # already holding
    assert not result.legal
    assert game.hands[Player.A] == 1
    assert game.turn_index == 2

  def test_illegal_place_wastes_turn(self) -> None:
    game = Game(2, ["A", "A", "A", "A"])
    game.step(Action(ActionKind.LIFT, 1))       # A lifts disk 1
    game.step(Action(ActionKind.PLACE, 2))      # A places on shared pole
    game.step(Action(ActionKind.LIFT, 1))       # A lifts disk 3
    result = game.step(Action(ActionKind.PLACE, 2))  # cannot place 3 on disk 1
    assert not result.legal
    assert game.hands[Player.A] == 3
    assert game.poles["2"] == [1]

  def test_shared_pole_visible_to_both(self) -> None:
    game = Game(1, ["A", "B", "A"])
    game.step(Action(ActionKind.LIFT, 1))
    game.step(Action(ActionKind.SKIP))
    game.step(Action(ActionKind.PLACE, 2))
    assert game.poles["2"] == [1]
    obs_b = game.observation(Player.B)
    assert obs_b["poles"][2] == [1]

  def test_either_player_can_lift_from_shared(self) -> None:
    game = Game(1, ["A", "B", "A", "B"])
    game.step(Action(ActionKind.LIFT, 1))
    game.step(Action(ActionKind.SKIP))
    game.step(Action(ActionKind.PLACE, 2))
    game.step(Action(ActionKind.LIFT, 2))
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
    game.step(Action(ActionKind.LIFT, 1))
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
    game = Game(1, ["A"])
    agent = RandomAgent(seed=0)
    action = agent.act(game)
    assert action in game.legal_actions()

  def test_uses_only_legal_moves(self) -> None:
    game = Game(2, ["A"] * 20)
    for _ in range(20):
      action = game.legal_actions()[0]
      assert game.is_legal(action)
      game.step(action)


class TestAgentsAndRunner:
  def test_scripted_agent_returns_moves_in_order(self) -> None:
    moves = [Action(ActionKind.LIFT, 1), Action(ActionKind.SKIP)]
    agent = ScriptedAgent(moves)
    game = Game(1, ["A", "A"])
    assert agent.act(game) == moves[0]
    assert agent.act(game) == moves[1]

  def test_episode_runner_with_scripted_agent(self) -> None:
    moves = [
      Action(ActionKind.LIFT, 1),
      Action(ActionKind.LIFT, 1),
      Action(ActionKind.PLACE, 3),
    ]
    game = Game(1, [Player.A, Player.B, Player.A])
    runner = EpisodeRunner.with_shared_agent(game, ScriptedAgent(moves))
    result = runner.run()
    assert result.winner == Player.A


class TestParseAction:
  def test_skip(self) -> None:
    assert parse_action("skip").kind == ActionKind.SKIP

  def test_lift(self) -> None:
    action = parse_action("lift", 2)
    assert action == Action(ActionKind.LIFT, 2)
