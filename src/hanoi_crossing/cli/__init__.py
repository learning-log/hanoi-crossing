"""CLI entry point for replay and random-play frontends."""

from __future__ import annotations

import argparse
import json
import sys

from hanoi_crossing.cli import random_cli, replay_cli
from hanoi_crossing.engine import Game
from hanoi_crossing.runner import run_random, run_replay, run_replay_file

__all__ = ["main", "run_random", "run_replay", "run_replay_file"]


def format_result(game: Game) -> str:
  snap = game.snapshot()
  winner = snap["winner"] or "none"
  return json.dumps(snap, indent=2) + f"\nWinner: {winner}\n"


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(prog="hanoi-crossing")
  sub = parser.add_subparsers(dest="command", required=True)
  replay_cli.add_parser(sub)
  random_cli.add_parser(sub)

  args = parser.parse_args(argv)

  try:
    game = args.run_command(args)
  except (ValueError, KeyError, json.JSONDecodeError) as exc:
    print(f"error: {exc}", file=sys.stderr)
    return 1

  print(format_result(game))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
