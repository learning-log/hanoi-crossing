"""Agents that select actions from the game engine."""

from __future__ import annotations

import random

from hanoi_crossing.engine import Game
from hanoi_crossing.types import Action, ActionKind


class Agent:
  """Placeholder for external policies (RL, heuristics, human input)."""


class RandomAgent(Agent):
  """Picks uniformly from the current player's legal actions."""

  def __init__(self, *, seed: int | None = None) -> None:
    self._rng = random.Random(seed)

  def act(self, game: Game) -> Action:
    return self._rng.choice(game.legal_actions())


class ScriptedAgent(Agent):
  """Returns the next pre-recorded move on each call to act."""

  def __init__(self, moves: list[Action]) -> None:
    self._moves = moves
    self._index = 0

  def act(self, game: Game) -> Action:
    if self._index >= len(self._moves):
      return Action(ActionKind.SKIP)
    action = self._moves[self._index]
    self._index += 1
    return action
