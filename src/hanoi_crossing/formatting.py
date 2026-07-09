"""Format engine state and episode traces for CLI output."""

from __future__ import annotations

import json
from typing import Any

from hanoi_crossing.engine import Game
from hanoi_crossing.types import StepTrace


def result_to_dict(
  engine: Game,
  *,
  traces: list[StepTrace] | None = None,
) -> dict[str, Any]:
  payload = engine.snapshot()
  if traces is not None:
    payload["traces"] = [
      {
        "turn_index": trace.turn_index,
        "expected_player": trace.expected_player.value,
        "acting_player": trace.acting_player.value,
        "action": _action_dict(trace.action),
        "valid": trace.valid,
        "done": trace.done,
        "winner": trace.winner.value if trace.winner else None,
        "reason": trace.reason,
        "observation": trace.observation,
        "legal_actions": [_action_dict(a) for a in trace.legal_actions],
      }
      for trace in traces
    ]
  return payload


def format_result(
  engine: Game,
  *,
  traces: list[StepTrace] | None = None,
) -> str:
  snap = engine.snapshot()
  winner = snap["winner"] or "none"
  lines = [json.dumps(snap, indent=2), f"Winner: {winner}"]
  if traces:
    lines.append("")
    lines.append(f"Trace ({len(traces)} steps):")
    for trace in traces:
      action = _action_dict(trace.action)
      lines.append(
        f"  turn {trace.turn_index}: {trace.acting_player.value} "
        f"{action['kind']}"
        f"{f' pole {action['pole']}' if action.get('pole') is not None else ''} "
        f"({'valid' if trace.valid else 'invalid'})"
      )
  return "\n".join(lines) + "\n"


def _action_dict(action: Any) -> dict[str, Any]:
  data: dict[str, Any] = {"kind": action.kind.value}
  if action.pole is not None:
    data["pole"] = action.pole
  return data
