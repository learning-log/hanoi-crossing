"""Shared data types for the Hanoi Crossing engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from hanoi_crossing.actions import Action

PlayerId = Literal["A", "B"]
PoleView = Literal["1", "2", "3"]

PLAYER_A: PlayerId = "A"
PLAYER_B: PlayerId = "B"

# Player-relative pole labels map to internal pole keys on the full board.
POLE_KEYS: dict[PlayerId, dict[PoleView, str]] = {
    "A": {"1": "1a", "2": "2", "3": "3a"},
    "B": {"1": "1b", "2": "2", "3": "3b"},
}


@dataclass(frozen=True)
class Observation:
    """What a single player can see before choosing an action."""

    player: PlayerId
    poles: dict[PoleView, tuple[int, ...]]
    hand: int | None


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
    """Authoritative full-board snapshot (both players' private poles included)."""

    poles: dict[str, list[int]] = field(default_factory=dict)
    hands: dict[PlayerId, int | None] = field(
        default_factory=lambda: {"A": None, "B": None}
    )

    def copy(self) -> BoardState:
        return BoardState(
            poles={k: list(v) for k, v in self.poles.items()},
            hands=dict(self.hands),
        )
