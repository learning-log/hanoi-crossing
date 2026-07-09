"""Core Hanoi Crossing game engine."""

from __future__ import annotations

from typing import Sequence

from hanoi_crossing.actions import Action, ActionKind
from hanoi_crossing.models import (
    POLE_KEYS,
    BoardSnapshot,
    BoardState,
    Observation,
    PoleView,
    PlayerId,
    StepResult,
    frozen_mapping,
)


def _initial_poles(n: int) -> dict[str, list[int]]:
    odds = list(range(2 * n - 1, 0, -2))  # largest odd on bottom
    evens = list(range(2 * n, 0, -2))
    return {
        "1a": odds,
        "1b": evens,
        "2": [],
        "3a": [],
        "3b": [],
    }


def _visible_poles(player: PlayerId) -> tuple[PoleView, ...]:
    return ("1", "2", "3")


def _pole_key(player: PlayerId, view: PoleView) -> str:
    return POLE_KEYS[player][view]


def _can_place(disk: int, pole: list[int]) -> bool:
    return not pole or pole[-1] > disk


def _check_win(state: BoardState, player: PlayerId) -> bool:
    if state.hands[player] is not None:
        return False
    mapping = POLE_KEYS[player]
    if state.poles[mapping["1"]] or state.poles[mapping["2"]]:
        return False
    return bool(state.poles[mapping["3"]])


def _find_winner(state: BoardState, *, acting_player: PlayerId) -> PlayerId | None:
    """Return the winner after a valid step, scanning both players.

    Tie-break: if both players satisfy the win condition simultaneously, the
    acting player is credited (see README § Win detection).
    """
    winners = [player for player in ("A", "B") if _check_win(state, player)]
    if not winners:
        return None
    if len(winners) == 1:
        return winners[0]
    return acting_player


class HanoiCrossingEngine:
    """Environment core for Hanoi Crossing.

    Orchestration (``EpisodeRunner``) calls :meth:`observe` and
    :meth:`legal_actions`, passes that data to agents, then applies the chosen
    action via :meth:`step`. Agents must not receive the engine handle — only
    serialized observations and legal-action lists (matching a remote RL/service
    boundary). Turn order is supplied externally and never inferred by the engine.
    """

    def __init__(
        self,
        n: int,
        *,
        turn_order: Sequence[PlayerId] | None = None,
        state: BoardState | None = None,
    ) -> None:
        if n < 1:
            raise ValueError("n must be >= 1")
        self.n = n
        self._turn_order = list(turn_order) if turn_order is not None else []
        self._turn_index = 0
        self._state = state.copy() if state is not None else BoardState(poles=_initial_poles(n))
        self._done = False
        self._winner: PlayerId | None = None
        self._snapshot_cache: BoardSnapshot | None = None

    @property
    def state(self) -> BoardSnapshot:
        if self._snapshot_cache is None:
            self._snapshot_cache = self._state.to_snapshot()
        return self._snapshot_cache

    def _invalidate_snapshot(self) -> None:
        self._snapshot_cache = None

    @property
    def done(self) -> bool:
        return self._done

    @property
    def winner(self) -> PlayerId | None:
        return self._winner

    @property
    def turn_index(self) -> int:
        return self._turn_index

    @property
    def turn_order(self) -> list[PlayerId]:
        return list(self._turn_order)

    @property
    def expected_player(self) -> PlayerId | None:
        if self._turn_index >= len(self._turn_order):
            return None
        return self._turn_order[self._turn_index]

    def observe(self, player: PlayerId) -> Observation:
        poles = {
            view: tuple(self._state.poles[_pole_key(player, view)])
            for view in _visible_poles(player)
        }
        return Observation(
            player=player,
            poles=frozen_mapping(poles),
            hand=self._state.hands[player],
        )

    def legal_actions(self, player: PlayerId) -> list[Action]:
        actions: list[Action] = [Action(ActionKind.SKIP)]
        hand = self._state.hands[player]
        for view in _visible_poles(player):
            key = _pole_key(player, view)
            stack = self._state.poles[key]
            if hand is None and stack:
                actions.append(Action(ActionKind.LIFT, view))
            elif hand is not None and _can_place(hand, stack):
                actions.append(Action(ActionKind.PLACE, view))
        return actions

    def step(self, player: PlayerId, action: Action) -> StepResult:
        observation = self.observe(player)
        legal_actions = tuple(self.legal_actions(player))
        turn_index = self._turn_index

        if self._done:
            return StepResult(
                False,
                True,
                self._winner,
                "game already finished",
                acting_player=player,
                action=action,
                observation=observation,
                legal_actions=legal_actions,
                turn_index=turn_index,
            )

        # Protocol violation (not an illegal move): soft-fail so agent loops keep
        # running. Replay uses strict validation upstream; see README §6.
        if self._turn_order and self.expected_player != player:
            expected = self.expected_player
            self._advance_turn()
            return StepResult(
                False,
                self._done,
                self._winner,
                f"expected player {expected}, got {player}",
                acting_player=player,
                action=action,
                observation=observation,
                legal_actions=legal_actions,
                turn_index=turn_index,
            )

        if action not in legal_actions:
            self._advance_turn()
            return StepResult(
                False,
                self._done,
                self._winner,
                "illegal action",
                acting_player=player,
                action=action,
                observation=observation,
                legal_actions=legal_actions,
                turn_index=turn_index,
            )

        self._apply_action(player, action)
        winner = _find_winner(self._state, acting_player=player)
        if winner is not None:
            self._done = True
            self._winner = winner
        self._advance_turn()
        return StepResult(
            True,
            self._done,
            self._winner,
            None,
            acting_player=player,
            action=action,
            observation=observation,
            legal_actions=legal_actions,
            turn_index=turn_index,
        )

    def _apply_action(self, player: PlayerId, action: Action) -> None:
        if action.kind is ActionKind.SKIP:
            return
        assert action.pole is not None
        key = _pole_key(player, action.pole)
        if action.kind is ActionKind.LIFT:
            disk = self._state.poles[key].pop()
            self._state.hands[player] = disk
        else:
            disk = self._state.hands[player]
            assert disk is not None
            self._state.poles[key].append(disk)
            self._state.hands[player] = None
        self._invalidate_snapshot()

    def _advance_turn(self) -> None:
        if self._turn_order:
            self._turn_index += 1

    def run(self, moves: Sequence[tuple[PlayerId, Action]]) -> PlayerId | None:
        """Apply a scripted sequence of (player, action) pairs."""
        for player, action in moves:
            if self._done:
                break
            self.step(player, action)
        return self._winner
