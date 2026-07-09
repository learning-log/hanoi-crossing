"""Random-play CLI — two random agents play until someone wins or steps run out."""

from __future__ import annotations

import argparse
import json
import random
import sys

from hanoi_crossing.agents import RandomAgent
from hanoi_crossing.engine import HanoiCrossingEngine
from hanoi_crossing.formatting import format_result, result_to_dict
from hanoi_crossing.models import PLAYER_A, PLAYER_B, PlayerId
from hanoi_crossing.runner import EpisodeRunner


def _random_turn_order(length: int, rng: random.Random) -> list[PlayerId]:
    return [rng.choice((PLAYER_A, PLAYER_B)) for _ in range(length)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Play Hanoi Crossing with random agents.")
    parser.add_argument("n", type=int, help="Disks per player")
    parser.add_argument(
        "--steps",
        type=int,
        default=200,
        help="Maximum turns before stopping (default: 200)",
    )
    parser.add_argument("--seed", type=int, default=None, help="RNG seed")
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
    args = parser.parse_args(argv)

    if args.n < 1:
        print("error: n must be >= 1", file=sys.stderr)
        return 1

    rng = random.Random(args.seed)
    turn_order = _random_turn_order(args.steps, rng)
    engine = HanoiCrossingEngine(args.n, turn_order=turn_order)
    runner = EpisodeRunner(engine)
    runner.run_agent(RandomAgent(rng))

    traces = runner.traces if args.trace else None
    if args.json:
        print(json.dumps(result_to_dict(engine, traces=traces), indent=2))
    else:
        print(format_result(engine, traces=traces))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
