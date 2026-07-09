"""CLI entry point for replay and random-play frontends."""

from __future__ import annotations

import argparse
import json
import sys

from hanoi_crossing.cli import random_cli, replay_cli
from hanoi_crossing.engine import Game
from hanoi_crossing.formatting import format_result, result_to_dict
from hanoi_crossing.cli.random_cli import run_random
from hanoi_crossing.cli.replay_cli import run_replay, run_replay_file

__all__ = ["main", "run_random", "run_replay", "run_replay_file"]


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(prog="hanoi-crossing")
  sub = parser.add_subparsers(dest="command", required=True)
  replay_cli.add_parser(sub)
  random_cli.add_parser(sub)

  args = parser.parse_args(argv)

  try:
    outcome = args.run_command(args)
  except (ValueError, KeyError, json.JSONDecodeError) as exc:
    print(f"error: {exc}", file=sys.stderr)
    return 1

  if isinstance(outcome, tuple):
    game, traces, cmd_args = outcome
    if cmd_args.json:
      print(json.dumps(result_to_dict(game, traces=traces), indent=2))
    else:
      print(format_result(game, traces=traces))
  else:
    print(format_result(outcome))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
