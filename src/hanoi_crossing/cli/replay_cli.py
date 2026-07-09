"""Replay CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from hanoi_crossing.engine import Game, parse_action
from hanoi_crossing.runner import EpisodeRunner, ReplayValidationError, validate_replay
from hanoi_crossing.types import Action, ActionKind, Player


def run_replay(
  n: int,
  turn_order: list[Player | str],
  moves: list[Action],
  *,
  scripted_players: list[Player] | None = None,
) -> Game:
  order = [Player(p) for p in turn_order]
  if scripted_players:
    pairs = list(zip(scripted_players, moves, strict=True))
    validate_replay(order, pairs)
  else:
    pairs = list(zip(order, moves, strict=False))

  engine = Game(n, order)
  EpisodeRunner(engine).run_scripted(pairs, strict=scripted_players is not None)
  return engine


def run_replay_file(path: Path) -> Game:
  n, turn_order, pairs = _load_replay_file(path)
  engine = Game(n, turn_order)
  EpisodeRunner(engine).run_scripted(pairs, strict=True)
  return engine


def _load_replay_file(path: Path) -> tuple[int, list[Player], list[tuple[Player, Action]]]:
  text = path.read_text()
  if path.suffix.lower() == ".json":
    data = json.loads(text)
    turn_order = [Player(p) for p in data["turn_order"]]
    actions = _parse_moves(data["moves"])
    pairs = list(zip(turn_order, actions, strict=True))
    validate_replay(turn_order, pairs)
    return int(data["n"]), turn_order, pairs

  n, turn_order, pairs = _parse_text_replay(text.splitlines())
  validate_replay(turn_order, pairs)
  return n, turn_order, pairs


def _parse_moves(raw_moves: list[dict[str, Any]]) -> list[Action]:
  actions: list[Action] = []
  for entry in raw_moves:
    kind = ActionKind(entry["action"])
    pole = entry.get("pole")
    if kind == ActionKind.SKIP:
      actions.append(Action(kind))
    else:
      if pole is None:
        raise ValueError(f"pole required for {kind.value}")
      actions.append(Action(kind, int(pole)))
  return actions


def _parse_text_replay(lines: list[str]) -> tuple[int, list[Player], list[tuple[Player, Action]]]:
  n: int | None = None
  turn_order: list[Player] = []
  scripted: list[tuple[Player, Action]] = []

  for lineno, raw in enumerate(lines, start=1):
    line = raw.strip()
    if not line or line.startswith("#"):
      continue
    parts = line.split()
    if parts[0].lower() == "n" and len(parts) == 2:
      n = int(parts[1])
      continue
    if parts[0].lower() == "turn" and len(parts) >= 2:
      turn_order = [Player(p) for p in parts[1:]]
      continue
    if parts[0] in ("A", "B") and len(parts) >= 2:
      player = Player(parts[0])
      action = parse_action(parts[1], int(parts[2]) if len(parts) > 2 else None)
      scripted.append((player, action))
      continue
    raise ValueError(f"line {lineno}: unrecognized syntax: {line}")

  if n is None:
    raise ValueError("missing 'n <disks>' line")
  if not turn_order:
    raise ValueError("missing 'turn ...' line")
  return n, turn_order, scripted


def add_parser(subparsers: argparse._SubParsersAction) -> None:
  parser = subparsers.add_parser("replay", help="replay moves from a file")
  parser.add_argument("file", type=Path, help="JSON or text replay file")
  parser.set_defaults(run_command=run_from_args)


def run_from_args(args: argparse.Namespace) -> Game:
  return run_replay_file(args.file)
