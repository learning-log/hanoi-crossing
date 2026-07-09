"""Episode orchestration — turn loop, replay loading, run helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from hanoi_crossing.agents import Agent, RandomAgent, ScriptedAgent
from hanoi_crossing.engine import Game, parse_action
from hanoi_crossing.types import Action, ActionKind, Player


def build_turn_order(max_turns: int, pattern: str = "ab") -> list[Player]:
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


class EpisodeRunner:
  """Runs a game episode by querying agents and stepping the engine."""

  def __init__(self, game: Game, agents: dict[Player, Agent]) -> None:
    self.game = game
    self.agents = agents

  @classmethod
  def with_shared_agent(cls, game: Game, agent: Agent) -> EpisodeRunner:
    return cls(game, {Player.A: agent, Player.B: agent})

  def run(self) -> Game:
    while self.game.has_more_turns():
      player = self.game.current_player()
      action = self.agents[player].act(self.game)
      self.game.step(action)
      if self.game.done:
        break
    return self.game


def run_random(
  n: int,
  max_turns: int,
  *,
  seed: int | None = None,
  turn_pattern: str = "ab",
) -> Game:
  game = Game(n, build_turn_order(max_turns, turn_pattern))
  return EpisodeRunner.with_shared_agent(game, RandomAgent(seed=seed)).run()


def run_replay(
  n: int,
  turn_order: list[Player | str],
  moves: list[Action],
  *,
  scripted_players: list[Player] | None = None,
) -> Game:
  order = [Player(p) for p in turn_order]
  if scripted_players:
    for idx, actor in enumerate(scripted_players):
      if idx < len(order) and actor != order[idx]:
        raise ValueError(
          f"turn {idx + 1}: move player {actor.value} does not match order {order[idx].value}"
        )
  game = Game(n, order)
  return EpisodeRunner.with_shared_agent(game, ScriptedAgent(moves)).run()


def run_replay_file(path: Path) -> Game:
  n, turn_order, moves, scripted_players = load_replay_file(path)
  return run_replay(n, turn_order, moves, scripted_players=scripted_players)


def load_replay_file(
  path: Path,
) -> tuple[int, list[Player], list[Action], list[Player] | None]:
  text = path.read_text()
  if path.suffix.lower() == ".json":
    data = json.loads(text)
    return (
      int(data["n"]),
      [Player(p) for p in data["turn_order"]],
      _parse_moves(data["moves"]),
      None,
    )

  n, turn_order, scripted = _parse_text_replay(text.splitlines())
  return (
    n,
    turn_order,
    [action for _, action in scripted],
    [player for player, _ in scripted],
  )


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
