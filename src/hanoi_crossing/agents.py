"""Agent protocol and reference policy implementations."""

from __future__ import annotations

import random
from typing import Protocol

from hanoi_crossing.actions import Action
from hanoi_crossing.engine import HanoiCrossingEngine
from hanoi_crossing.models import PlayerId


class Agent(Protocol):
    """External policy interface — random, RL, and LLM agents implement this."""

    def act(self, engine: HanoiCrossingEngine, player: PlayerId) -> Action:
        """Choose an action from the player's current observation."""
        ...


class RandomAgent:
    """Uniform random choice over legal actions."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    def act(self, engine: HanoiCrossingEngine, player: PlayerId) -> Action:
        return self._rng.choice(engine.legal_actions(player))


class ScriptedAgent:
    """Plays a fixed action list; turn order selects the acting player."""

    def __init__(self, actions: list[Action]) -> None:
        self._actions = list(actions)
        self._index = 0

    def act(self, engine: HanoiCrossingEngine, player: PlayerId) -> Action:
        if self._index >= len(self._actions):
            return engine.legal_actions(player)[0]
        action = self._actions[self._index]
        self._index += 1
        return action
