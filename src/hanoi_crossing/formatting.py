"""CLI and serialization helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hanoi_crossing.actions import Action, parse_action, parse_player
from hanoi_crossing.engine import HanoiCrossingEngine
from hanoi_crossing.models import BoardSnapshot, Observation, PlayerId, StepTrace


def format_board(state: BoardSnapshot) -> str:
    lines = ["Board:"]
    for pole in ("1a", "2", "3a", "1b", "3b"):
        disks = state.poles.get(pole, [])
        label = pole if disks else f"{pole} (empty)"
        lines.append(f"  {label}: {disks}")
    lines.append(f"  hands: A={state.hands['A']}, B={state.hands['B']}")
    return "\n".join(lines)


def format_observation(obs: Observation) -> str:
    pole_bits = ", ".join(f"{k}={list(obs.poles[k])}" for k in ("1", "2", "3"))
    hand = "empty" if obs.hand is None else str(obs.hand)
    return f"Player {obs.player}: poles [{pole_bits}], hand={hand}"


def state_to_dict(state: BoardSnapshot) -> dict[str, Any]:
    return {
        "poles": {k: list(v) for k, v in state.poles.items()},
        "hands": dict(state.hands),
    }


def observation_to_dict(obs: Observation) -> dict[str, Any]:
    return {
        "player": obs.player,
        "poles": {k: list(obs.poles[k]) for k in ("1", "2", "3")},
        "hand": obs.hand,
    }


def action_to_dict(action: Action) -> dict[str, Any]:
    return {"kind": action.kind.value, "pole": action.pole}


def trace_to_dict(trace: StepTrace) -> dict[str, Any]:
    return {
        "turn_index": trace.turn_index,
        "expected_player": trace.expected_player,
        "acting_player": trace.acting_player,
        "action": str(trace.action),
        "valid": trace.valid,
        "done": trace.done,
        "winner": trace.winner,
        "reason": trace.reason,
        "observation": observation_to_dict(trace.observation),
        "legal_actions": [str(action) for action in trace.legal_actions],
    }


def format_trace(trace: StepTrace) -> str:
    status = "ok" if trace.valid else f"INVALID ({trace.reason})"
    parts = [
        f"[{trace.turn_index + 1}] {trace.acting_player} -> {trace.action} [{status}]",
        f"  expected: {trace.expected_player}",
        f"  legal: {[str(a) for a in trace.legal_actions]}",
        f"  obs: {format_observation(trace.observation)}",
    ]
    if trace.done and trace.winner:
        parts.append(f"  winner: {trace.winner}")
    return "\n".join(parts)


def format_traces(traces: list[StepTrace]) -> str:
    if not traces:
        return "Trace: (empty)"
    lines = ["Trace:"]
    lines.extend(format_trace(trace) for trace in traces)
    return "\n".join(lines)


def result_to_dict(
    engine: HanoiCrossingEngine,
    traces: list[StepTrace] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "n": engine.n,
        "done": engine.done,
        "winner": engine.winner,
        "turn_index": engine.turn_index,
        "state": state_to_dict(engine.state),
    }
    if traces is not None:
        payload["trace"] = [trace_to_dict(trace) for trace in traces]
    return payload


def format_result(
    engine: HanoiCrossingEngine,
    traces: list[StepTrace] | None = None,
) -> str:
    parts = [format_board(engine.state)]
    if traces:
        parts.append(format_traces(traces))
    if engine.winner:
        parts.append(f"Winner: Player {engine.winner}")
    elif engine.done:
        parts.append("Game over (no winner recorded).")
    else:
        parts.append("Game in progress.")
    return "\n".join(parts)


def parse_replay_text(text: str) -> tuple[int, list[PlayerId], list[tuple[PlayerId, Action]]]:
    n: int | None = None
    turn_order: list[PlayerId] = []
    moves: list[tuple[PlayerId, Action]] = []

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("n "):
            n = int(line.split()[1])
            continue
        if line.lower().startswith("turn "):
            turn_order = [parse_player(p) for p in line.split()[1:]]
            continue
        if line.lower().startswith("move "):
            parts = line.split(maxsplit=2)
            if len(parts) != 3:
                raise ValueError(f"bad move line: {raw!r}")
            player = parse_player(parts[1])
            action = parse_action(parts[2])
            moves.append((player, action))
            continue
        raise ValueError(f"unrecognized replay line: {raw!r}")

    if n is None:
        raise ValueError("replay file must include 'n <disks>'")
    return n, turn_order, moves


def parse_replay_json(data: dict[str, Any]) -> tuple[int, list[PlayerId], list[tuple[PlayerId, Action]]]:
    n = int(data["n"])
    turn_order = [parse_player(p) for p in data["turn_order"]]
    moves = [(parse_player(m["player"]), parse_action(m["action"])) for m in data["moves"]]
    return n, turn_order, moves


def load_replay(path: Path) -> tuple[int, list[PlayerId], list[tuple[PlayerId, Action]]]:
    text = path.read_text()
    if path.suffix == ".json":
        return parse_replay_json(json.loads(text))
    return parse_replay_text(text)
