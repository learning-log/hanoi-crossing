"""Shared types for the Hanoi Crossing engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Player(str, Enum):
    A = "A"
    B = "B"


class ActionKind(str, Enum):
    SKIP = "skip"
    LIFT = "lift"
    PLACE = "place"


@dataclass(frozen=True)
class Action:
    kind: ActionKind
    pole: Optional[int] = None  # 1, 2, or 3 in the acting player's view


@dataclass
class StepResult:
    legal: bool
    done: bool
    winner: Optional[Player] = None


# Local pole number (1/2/3) -> internal pole id for each player.
POLE_MAP: dict[Player, dict[int, str]] = {
    Player.A: {1: "1a", 2: "2", 3: "3a"},
    Player.B: {1: "1b", 2: "2", 3: "3b"},
}

ALL_POLE_IDS = ("1a", "2", "3a", "1b", "3b")
