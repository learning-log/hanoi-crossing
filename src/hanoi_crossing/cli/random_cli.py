"""Random-play CLI."""

from __future__ import annotations

import argparse

from hanoi_crossing.engine import Game
from hanoi_crossing.runner import run_random


def add_parser(subparsers: argparse._SubParsersAction) -> None:
  parser = subparsers.add_parser("random", help="play out random legal moves")
  parser.add_argument("--n", type=int, required=True, help="disks per player")
  parser.add_argument("--turns", type=int, default=200, help="max turns")
  parser.add_argument("--seed", type=int, default=None)
  parser.add_argument(
    "--pattern",
    default="ab",
    help="turn order pattern: ab (default), a, b, or custom like ABBA",
  )
  parser.set_defaults(run_command=run_from_args)


def run_from_args(args: argparse.Namespace) -> Game:
  return run_random(args.n, args.turns, seed=args.seed, turn_pattern=args.pattern)
