"""Action representation and parsing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from hanoi_crossing.models import PoleView, PlayerId


class ActionKind(str, Enum):
    SKIP = "skip"
    LIFT = "lift"
    PLACE = "place"


@dataclass(frozen=True, slots=True)
class Action:
    kind: ActionKind
    pole: PoleView | None = None

    def __str__(self) -> str:
        if self.kind is ActionKind.SKIP:
            return "skip"
        return f"{self.kind.value} {self.pole}"


def parse_action(line: str) -> Action:
    """Parse one action line: ``skip``, ``lift <pole>``, or ``place <pole>``."""
    parts = line.strip().lower().split()
    if not parts:
        raise ValueError("empty action line")
    kind = ActionKind(parts[0])
    if kind is ActionKind.SKIP:
        if len(parts) != 1:
            raise ValueError(f"skip takes no arguments: {line!r}")
        return Action(kind=kind)
    if len(parts) != 2 or parts[1] not in {"1", "2", "3"}:
        raise ValueError(f"expected lift|place <1|2|3>: {line!r}")
    return Action(kind=kind, pole=parts[1])  # type: ignore[arg-type]


def parse_player(line: str) -> PlayerId:
    player = line.strip().upper()
    if player not in {"A", "B"}:
        raise ValueError(f"invalid player: {line!r}")
    return player  # type: ignore[return-value]


def format_actions(actions: Iterable[Action]) -> list[str]:
    return [str(action) for action in actions]
