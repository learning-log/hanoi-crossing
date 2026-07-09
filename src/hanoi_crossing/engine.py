"""Core Hanoi Crossing game engine."""

from __future__ import annotations

import copy
from typing import Any, Optional

from hanoi_crossing.types import (
    ALL_POLE_IDS,
    POLE_MAP,
    Action,
    ActionKind,
    Player,
    StepResult,
)


def _initial_pole_stacks(n: int) -> dict[str, list[int]]:
  """Build starting stacks: odds on 1a, evens on 1b, shared pole empty."""
  odds = [2 * i - 1 for i in range(n, 0, -1)]
  evens = [2 * i for i in range(n, 0, -1)]
  return {
    "1a": odds,
    "2": [],
    "3a": [],
    "1b": evens,
    "3b": [],
  }


class Game:
  """Turn-based Hanoi Crossing environment.

  Designed as a reusable core: agents call ``legal_actions`` and ``step``;
  frontends and RL loops supply turn order externally.
  """

  def __init__(self, n: int, turn_order: list[Player | str]) -> None:
    if n < 1:
      raise ValueError("n must be >= 1")
    self.n = n
    self.turn_order = [Player(p) for p in turn_order]
    self.turn_index = 0
    self.poles: dict[str, list[int]] = _initial_pole_stacks(n)
    self.hands: dict[Player, Optional[int]] = {Player.A: None, Player.B: None}
    self.winner: Optional[Player] = None

  # -- queries ----------------------------------------------------------------

  @property
  def done(self) -> bool:
    return self.winner is not None

  def current_player(self) -> Player:
    if not self.turn_order:
      raise RuntimeError("empty turn_order")
    idx = min(self.turn_index, len(self.turn_order) - 1)
    return self.turn_order[idx]

  def has_more_turns(self) -> bool:
    return self.turn_index < len(self.turn_order) and not self.done

  def visible_pole_ids(self, player: Player) -> tuple[str, str, str]:
    mapping = POLE_MAP[player]
    return mapping[1], mapping[2], mapping[3]

  def observation(self, player: Player) -> dict[str, Any]:
    """Player-local view: own poles, shared pole, own hand. Opponent hand hidden."""
    p1, p2, p3 = self.visible_pole_ids(player)
    return {
      "player": player.value,
      "poles": {
        1: list(self.poles[p1]),
        2: list(self.poles[p2]),
        3: list(self.poles[p3]),
      },
      "hand": self.hands[player],
    }

  def snapshot(self) -> dict[str, Any]:
    """Full state for replay output and debugging."""
    return {
      "n": self.n,
      "poles": {pid: list(stack) for pid, stack in self.poles.items()},
      "hands": {p.value: self.hands[p] for p in Player},
      "turn_index": self.turn_index,
      "winner": self.winner.value if self.winner else None,
    }

  def clone(self) -> Game:
    """Deep copy for search / RL rollouts."""
    other = Game(self.n, self.turn_order)
    other.turn_index = self.turn_index
    other.poles = copy.deepcopy(self.poles)
    other.hands = dict(self.hands)
    other.winner = self.winner
    return other

  # -- rules ------------------------------------------------------------------

  def _can_place(self, disk: int, pole_id: str) -> bool:
    stack = self.poles[pole_id]
    return not stack or stack[-1] > disk

  def _check_winner(self) -> Optional[Player]:
    for player in Player:
      if self.hands[player] is not None:
        continue
      p1, p2, p3 = self.visible_pole_ids(player)
      if self.poles[p1] or self.poles[p2]:
        continue
      if self.poles[p3]:
        return player
    return None

  def legal_actions(self, player: Optional[Player] = None) -> list[Action]:
    player = player or self.current_player()
    actions: list[Action] = [Action(ActionKind.SKIP)]
    mapping = POLE_MAP[player]
    hand = self.hands[player]

    if hand is None:
      for local in (1, 2, 3):
        if self.poles[mapping[local]]:
          actions.append(Action(ActionKind.LIFT, local))
    else:
      for local in (1, 2, 3):
        if self._can_place(hand, mapping[local]):
          actions.append(Action(ActionKind.PLACE, local))
    return actions

  def is_legal(self, action: Action, player: Optional[Player] = None) -> bool:
    return action in self.legal_actions(player)

  # -- stepping ---------------------------------------------------------------

  def step(self, action: Action, *, player: Optional[Player] = None) -> StepResult:
    """Apply one action for the current turn. Illegal moves waste the turn."""
    if self.done:
      return StepResult(legal=False, done=True, winner=self.winner)

    if not self.has_more_turns():
      return StepResult(legal=False, done=self.done, winner=self.winner)

    actor = player or self.current_player()
    if actor != self.current_player():
      self.turn_index += 1
      return StepResult(legal=False, done=False, winner=None)

    legal = self._apply(actor, action)
    if legal:
      self.winner = self._check_winner()

    self.turn_index += 1
    return StepResult(legal=legal, done=self.done, winner=self.winner)

  def _apply(self, player: Player, action: Action) -> bool:
    if action.kind == ActionKind.SKIP:
      return True

    if action.pole not in (1, 2, 3):
      return False

    pole_id = POLE_MAP[player][action.pole]

    if action.kind == ActionKind.LIFT:
      if self.hands[player] is not None or not self.poles[pole_id]:
        return False
      self.hands[player] = self.poles[pole_id].pop()
      return True

    if action.kind == ActionKind.PLACE:
      disk = self.hands[player]
      if disk is None or not self._can_place(disk, pole_id):
        return False
      self.poles[pole_id].append(disk)
      self.hands[player] = None
      return True

    return False


def parse_action(raw: str, pole: Optional[int] = None) -> Action:
  """Parse action strings used by the text replay format."""
  kind = ActionKind(raw.lower())
  if kind == ActionKind.SKIP:
    return Action(kind)
  if pole is None:
    raise ValueError(f"pole required for action {raw}")
  return Action(kind, pole)
