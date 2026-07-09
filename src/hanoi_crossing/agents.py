"""Agents that select actions from the game engine."""

from __future__ import annotations

import random

from hanoi_crossing.engine import Game
from hanoi_crossing.types import Action, Player


class Agent:
  """Placeholder for external policies (RL, heuristics, human input)."""

  def act(self, engine: Game, player: Player) -> Action:
    raise NotImplementedError


class RandomAgent(Agent):
  """Picks uniformly from the acting player's legal actions."""

  def __init__(self, rng: random.Random) -> None:
    self._rng = rng

  def act(self, engine: Game, player: Player) -> Action:
    return self._rng.choice(engine.legal_actions(player))
