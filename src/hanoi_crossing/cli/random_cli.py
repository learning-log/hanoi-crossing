"""Random-play CLI — two random agents play until someone wins or steps run out."""

from __future__ import annotations

import argparse
import json
import random
import sys

from hanoi_crossing.agents import RandomAgent
from hanoi_crossing.engine import Game
from hanoi_crossing.formatting import format_result, result_to_dict
from hanoi_crossing.runner import EpisodeRunner
from hanoi_crossing.types import PLAYER_A, PLAYER_B, Player


def _random_turn_order(length: int, rng: random.Random) -> list[Player]:
  return [rng.choice((PLAYER_A, PLAYER_B)) for _ in range(length)]


def run_random(
  n: int,
  max_turns: int,
  *,
  seed: int | None = None,
  turn_pattern: str | None = None,
) -> Game:
  """Run a random episode and return the final engine state."""
  rng = random.Random(seed)
  if turn_pattern is not None:
    turn_order = _pattern_turn_order(max_turns, turn_pattern)
  else:
    turn_order = _random_turn_order(max_turns, rng)
  engine = Game(n, turn_order)
  EpisodeRunner(engine).run_agent(RandomAgent(rng))
  return engine


def _pattern_turn_order(max_turns: int, pattern: str) -> list[Player]:
  if max_turns < 1:
    raise ValueError("max_turns must be >= 1")
  if pattern == "ab":
    return [Player.A if i % 2 == 0 else Player.B for i in range(max_turns)]
  if pattern == "a":
    return [Player.A] * max_turns
  if pattern == "b":
    return [Player.B] * max_turns
  order = [Player(c.upper()) for c in pattern]
  if len(order) < max_turns:
    order = (order * ((max_turns // len(order)) + 1))[:max_turns]
  return order


def add_parser(subparsers: argparse._SubParsersAction) -> None:
  parser = subparsers.add_parser("random", help="play out random legal moves")
  parser.add_argument("--n", type=int, required=True, help="disks per player")
  parser.add_argument(
    "--steps",
    "--turns",
    dest="steps",
    type=int,
    default=200,
    help="maximum turns before stopping (default: 200)",
  )
  parser.add_argument("--seed", type=int, default=None, help="RNG seed")
  parser.add_argument(
    "--pattern",
    default=None,
    help="optional fixed turn pattern: ab, a, b, or custom like ABBA",
  )
  parser.add_argument(
    "--json",
    action="store_true",
    help="emit machine-readable JSON instead of text",
  )
  parser.add_argument(
    "--trace",
    action="store_true",
    help="include per-step decision trace in output",
  )
  parser.set_defaults(run_command=run_from_args)


def run_from_args(args: argparse.Namespace) -> tuple[Game, list | None, argparse.Namespace]:
  if args.n < 1:
    raise ValueError("n must be >= 1")

  rng = random.Random(args.seed)
  if args.pattern is not None:
    turn_order = _pattern_turn_order(args.steps, args.pattern)
  else:
    turn_order = _random_turn_order(args.steps, rng)

  engine = Game(args.n, turn_order)
  runner = EpisodeRunner(engine)
  runner.run_agent(RandomAgent(rng))

  traces = runner.traces if args.trace else None
  return engine, traces, args


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description="Play Hanoi Crossing with random agents.")
  parser.add_argument("n", type=int, help="disks per player")
  parser.add_argument(
    "--steps",
    type=int,
    default=200,
    help="maximum turns before stopping (default: 200)",
  )
  parser.add_argument("--seed", type=int, default=None, help="RNG seed")
  parser.add_argument(
    "--json",
    action="store_true",
    help="emit machine-readable JSON instead of text",
  )
  parser.add_argument(
    "--trace",
    action="store_true",
    help="include per-step decision trace in output",
  )
  args = parser.parse_args(argv)

  if args.n < 1:
    print("error: n must be >= 1", file=sys.stderr)
    return 1

  rng = random.Random(args.seed)
  engine = Game(args.n, _random_turn_order(args.steps, rng))
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
