"""CLI frontends: replay pre-recorded games and random self-play."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any, Iterable

from hanoi_crossing.engine import Game, parse_action
from hanoi_crossing.types import Action, ActionKind, Player


def _load_json(path: Path) -> dict[str, Any]:
  with path.open() as f:
    return json.load(f)


def _parse_turn_order(raw: Iterable[str]) -> list[Player]:
  return [Player(p) for p in raw]


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
  """Parse the line-oriented replay format documented in README."""
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
      turn_order = _parse_turn_order(parts[1:])
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


def run_replay(
  n: int,
  turn_order: list[Player],
  moves: list[Action],
  *,
  scripted_players: list[Player] | None = None,
) -> Game:
  game = Game(n, turn_order)
  for idx, action in enumerate(moves):
    expected = turn_order[idx] if idx < len(turn_order) else None
    actor = scripted_players[idx] if scripted_players else expected
    if actor is None:
      break
    if expected is not None and actor != expected:
      raise ValueError(
        f"turn {idx + 1}: move player {actor.value} does not match order {expected.value}"
      )
    game.step(action, player=actor)
    if game.done:
      break
  return game


def run_replay_file(path: Path) -> Game:
  text = path.read_text()
  if path.suffix.lower() == ".json":
    data = json.loads(text)
    n = int(data["n"])
    turn_order = _parse_turn_order(data["turn_order"])
    moves = _parse_moves(data["moves"])
    return run_replay(n, turn_order, moves)

  lines = text.splitlines()
  n, turn_order, scripted = _parse_text_replay(lines)
  return run_replay(
    n,
    turn_order,
    [action for _, action in scripted],
    scripted_players=[player for player, _ in scripted],
  )


def run_random(
  n: int,
  max_turns: int,
  *,
  seed: int | None = None,
  turn_pattern: str = "ab",
) -> Game:
  rng = random.Random(seed)
  if max_turns < 1:
    raise ValueError("max_turns must be >= 1")

  if turn_pattern == "ab":
    turn_order = [Player.A if i % 2 == 0 else Player.B for i in range(max_turns)]
  elif turn_pattern == "a":
    turn_order = [Player.A] * max_turns
  elif turn_pattern == "b":
    turn_order = [Player.B] * max_turns
  else:
    turn_order = [Player(c.upper()) for c in turn_pattern]
    if len(turn_order) < max_turns:
      turn_order = (turn_order * ((max_turns // len(turn_order)) + 1))[:max_turns]

  game = Game(n, turn_order)
  while game.has_more_turns():
    action = rng.choice(game.legal_actions())
    game.step(action)
    if game.done:
      break
  return game


def _format_result(game: Game) -> str:
  snap = game.snapshot()
  winner = snap["winner"] or "none"
  return json.dumps(snap, indent=2) + f"\nWinner: {winner}\n"


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(prog="hanoi-crossing")
  sub = parser.add_subparsers(dest="command", required=True)

  replay = sub.add_parser("replay", help="replay moves from a file")
  replay.add_argument("file", type=Path, help="JSON or text replay file")

  random_p = sub.add_parser("random", help="play out random legal moves")
  random_p.add_argument("--n", type=int, required=True, help="disks per player")
  random_p.add_argument("--turns", type=int, default=200, help="max turns")
  random_p.add_argument("--seed", type=int, default=None)
  random_p.add_argument(
    "--pattern",
    default="ab",
    help="turn order pattern: ab (default), a, b, or custom like ABBA",
  )

  args = parser.parse_args(argv)

  try:
    if args.command == "replay":
      game = run_replay_file(args.file)
    else:
      game = run_random(args.n, args.turns, seed=args.seed, turn_pattern=args.pattern)
  except (ValueError, KeyError, json.JSONDecodeError) as exc:
    print(f"error: {exc}", file=sys.stderr)
    return 1

  print(_format_result(game))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
