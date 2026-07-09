"""Agent protocol and reference policy implementations."""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import Protocol

from hanoi_crossing.actions import Action
from hanoi_crossing.models import Observation


class Agent(Protocol):
    """External policy interface — random, RL, and LLM agents implement this."""

    def act(self, observation: Observation, legal_actions: Sequence[Action]) -> Action:
        """Choose an action from the player's current observation and legal moves."""
        ...


class RandomAgent:
    """Uniform random choice over legal actions."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    def act(self, observation: Observation, legal_actions: Sequence[Action]) -> Action:
        return self._rng.choice(legal_actions)


class ScriptedAgent:
    """Plays a fixed action list; turn order selects the acting player."""

    def __init__(self, actions: list[Action]) -> None:
        self._actions = list(actions)
        self._index = 0

    def act(self, observation: Observation, legal_actions: Sequence[Action]) -> Action:
        if self._index >= len(self._actions):
            return legal_actions[0]
        action = self._actions[self._index]
        self._index += 1
        return action
