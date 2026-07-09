"""Replay CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from hanoi_crossing.engine import Game
from hanoi_crossing.runner import run_replay, run_replay_file


def add_parser(subparsers: argparse._SubParsersAction) -> None:
  parser = subparsers.add_parser("replay", help="replay moves from a file")
  parser.add_argument("file", type=Path, help="JSON or text replay file")
  parser.set_defaults(run_command=run_from_args)


def run_from_args(args: argparse.Namespace) -> Game:
  return run_replay_file(args.file)
