"""Shared data types for the Hanoi Crossing engine."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, TypeVar

if TYPE_CHECKING:
    from hanoi_crossing.actions import Action

PlayerId = Literal["A", "B"]
PoleView = Literal["1", "2", "3"]

PLAYER_A: PlayerId = "A"
PLAYER_B: PlayerId = "B"

K = TypeVar("K")
V = TypeVar("V")

# Player-relative pole labels map to internal pole keys on the full board.
POLE_KEYS: dict[PlayerId, dict[PoleView, str]] = {
    "A": {"1": "1a", "2": "2", "3": "3a"},
    "B": {"1": "1b", "2": "2", "3": "3b"},
}


def frozen_mapping(d: dict[K, V]) -> Mapping[K, V]:
    """Return a read-only view over a dict (stdlib MappingProxyType)."""
    return MappingProxyType(d)


@dataclass(frozen=True)
class Observation:
    """What a single player can see before choosing an action."""

    player: PlayerId
    poles: Mapping[PoleView, tuple[int, ...]]
    hand: int | None


@dataclass(frozen=True)
class BoardSnapshot:
    """Immutable read-only view of the full board for logging and tests."""

    poles: Mapping[str, tuple[int, ...]]
    hands: Mapping[PlayerId, int | None]


@dataclass(frozen=True)
class EngineSnapshot:
    """Full engine checkpoint for faithful save/restore."""

    n: int
    turn_order: tuple[PlayerId, ...]
    turn_index: int
    done: bool
    winner: PlayerId | None
    board: BoardSnapshot


@dataclass(frozen=True)
class StepResult:
    """Outcome of applying one action for the acting player."""

    valid: bool
    done: bool
    winner: PlayerId | None
    reason: str | None = None
    acting_player: PlayerId | None = None
    action: "Action | None" = None
    observation: Observation | None = None
    legal_actions: tuple["Action", ...] = ()
    turn_index: int = 0


@dataclass(frozen=True)
class StepTrace:
    """One decision point in an episode, suitable for eval logs and replay audit."""

    turn_index: int
    expected_player: PlayerId | None
    acting_player: PlayerId
    action: "Action"
    valid: bool
    done: bool
    winner: PlayerId | None
    reason: str | None
    observation: Observation
    legal_actions: tuple["Action", ...]


@dataclass
class BoardState:
    """Authoritative mutable full-board state (engine internal use only)."""

    poles: dict[str, list[int]] = field(default_factory=dict)
    hands: dict[PlayerId, int | None] = field(
        default_factory=lambda: {"A": None, "B": None}
    )

    def copy(self) -> BoardState:
        return BoardState(
            poles={k: list(v) for k, v in self.poles.items()},
            hands=dict(self.hands),
        )

    def to_snapshot(self) -> BoardSnapshot:
        return BoardSnapshot(
            poles=frozen_mapping({k: tuple(v) for k, v in self.poles.items()}),
            hands=frozen_mapping(dict(self.hands)),
        )

    @classmethod
    def from_snapshot(cls, snap: BoardSnapshot) -> BoardState:
        return cls(
            poles={k: list(v) for k, v in snap.poles.items()},
            hands=dict(snap.hands),
        )
