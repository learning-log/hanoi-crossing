"""Episode orchestration for agents and scripted replays."""

from __future__ import annotations

from dataclasses import dataclass, field

from hanoi_crossing.actions import Action
from hanoi_crossing.agents import Agent
from hanoi_crossing.engine import HanoiCrossingEngine
from hanoi_crossing.models import PlayerId, StepTrace


class ReplayValidationError(ValueError):
    """Raised when a replay file disagrees with the configured turn order."""


def validate_replay(
    turn_order: list[PlayerId],
    moves: list[tuple[PlayerId, Action]],
) -> None:
    """Ensure each scripted move matches the external turn order."""
    if not turn_order:
        return
    limit = min(len(turn_order), len(moves))
    for index in range(limit):
        expected = turn_order[index]
        actual, _ = moves[index]
        if actual != expected:
            raise ReplayValidationError(
                f"move {index + 1}: turn order expects {expected}, replay says {actual}"
            )
    if len(moves) > len(turn_order):
        extra = len(moves) - len(turn_order)
        raise ReplayValidationError(
            f"replay has {extra} more move(s) than entries in turn order"
        )


@dataclass
class EpisodeRunner:
    """Runs episodes while collecting per-step traces for evaluation."""

    engine: HanoiCrossingEngine
    traces: list[StepTrace] = field(default_factory=list)

    def reset_traces(self) -> None:
        self.traces.clear()

    def run_turn(self, player: PlayerId, action: Action) -> None:
        expected = self.engine.expected_player
        observation = self.engine.observe(player)
        legal_actions = tuple(self.engine.legal_actions(player))
        result = self.engine.step(player, action)
        self.traces.append(
            StepTrace(
                turn_index=result.turn_index,
                expected_player=expected,
                acting_player=player,
                action=action,
                valid=result.valid,
                done=result.done,
                winner=result.winner,
                reason=result.reason,
                observation=observation,
                legal_actions=legal_actions,
            )
        )

    def run_agent(self, agent: Agent, *, max_steps: int | None = None) -> PlayerId | None:
        """Run until the game ends or the turn schedule is exhausted."""
        steps = 0
        while not self.engine.done and self.engine.expected_player is not None:
            if max_steps is not None and steps >= max_steps:
                break
            player = self.engine.expected_player
            observation = self.engine.observe(player)
            legal_actions = self.engine.legal_actions(player)
            action = agent.act(observation, legal_actions)
            self.run_turn(player, action)
            steps += 1
        return self.engine.winner

    def run_scripted(
        self,
        moves: list[tuple[PlayerId, Action]],
        *,
        strict: bool = False,
    ) -> PlayerId | None:
        """Apply a fixed list of player/action pairs."""
        if strict:
            validate_replay(self.engine.turn_order, moves)
        for player, action in moves:
            if self.engine.done:
                break
            self.run_turn(player, action)
        return self.engine.winner
