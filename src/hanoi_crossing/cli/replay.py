"""Replay CLI — run a pre-recorded game and print the final state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hanoi_crossing.engine import HanoiCrossingEngine
from hanoi_crossing.formatting import format_result, load_replay, result_to_dict
from hanoi_crossing.runner import EpisodeRunner, ReplayValidationError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay a Hanoi Crossing game.")
    parser.add_argument("replay", type=Path, help="Replay file (.txt or .json)")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Include per-step decision trace in output",
    )
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Do not validate move players against turn order",
    )
    args = parser.parse_args(argv)

    try:
        n, turn_order, moves = load_replay(args.replay)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    engine = HanoiCrossingEngine(n, turn_order=turn_order)
    runner = EpisodeRunner(engine)

    try:
        runner.run_scripted(moves, strict=not args.no_strict)
    except ReplayValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    traces = runner.traces if args.trace else None
    if args.json:
        print(json.dumps(result_to_dict(engine, traces=traces), indent=2))
    else:
        print(format_result(engine, traces=traces))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
