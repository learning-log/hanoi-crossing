"""Hanoi Crossing — two-player cooperative-competitive Tower of Hanoi variant."""

from hanoi_crossing.agents import Agent, RandomAgent
from hanoi_crossing.engine import Game, parse_action
from hanoi_crossing.runner import EpisodeRunner, ReplayValidationError, validate_replay
from hanoi_crossing.types import (
  Action,
  ActionKind,
  Player,
  StepResult,
  StepTrace,
  PLAYER_A,
  PLAYER_B,
)

__all__ = [
  "Action",
  "ActionKind",
  "Agent",
  "EpisodeRunner",
  "Game",
  "PLAYER_A",
  "PLAYER_B",
  "Player",
  "RandomAgent",
  "ReplayValidationError",
  "StepResult",
  "StepTrace",
  "parse_action",
  "validate_replay",
]
