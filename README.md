# Hanoi Crossing

Two-player Tower of Hanoi variant with a shared middle pole. Each player has
three poles; pole 2 is shared and visible to both. Players start with `N` disks
on their pole 1 (A: odd sizes, B: even sizes) and win by moving all their disks
to pole 3 with an empty hand while poles 1 and 2 are clear.

**Full architecture, design patterns, and semantics:** see [design.md](design.md).

## Quick start

Requires [uv](https://docs.astral.sh/uv/) and **Python 3.11+**.

```bash
uv sync --dev
uv run pytest

# Replay a recorded game
uv run hanoi-crossing replay examples/n1_win.txt

# Random self-play (random turn order, uniform legal moves)
uv run hanoi-crossing random 2 --steps 100 --seed 1

# Optional: --json for machine-readable output, --trace for per-step logs
uv run hanoi-crossing replay examples/n1_win.txt --trace
```

Equivalent module invocations:

```bash
uv run python -m hanoi_crossing.cli.replay examples/n1_win.txt
uv run python -m hanoi_crossing.cli.random_play 2 --steps 100 --seed 1
```

## Board layout

```
        1a
        |
 1b -- [2] -- 3b
        |
        3a
```

- **Player A** sees poles `1 → 1a`, `2 → shared`, `3 → 3a`
- **Player B** sees poles `1 → 1b`, `2 → shared`, `3 → 3b`

Players never observe the opponent's private poles or the opponent's hand.

## Architecture (summary)

| Layer | Module | Role |
|-------|--------|------|
| Engine | `HanoiCrossingEngine` | Rules, `observe`, `legal_actions`, `step` |
| Agents | `Agent`, `RandomAgent`, `ScriptedAgent` | `act(observation, legal_actions) → Action` |
| Orchestration | `EpisodeRunner` | Episode loop, eval traces, replay validation |
| I/O | `formatting.py` | Replay parsing, JSON/text output |

Agents receive **only** an `Observation` and legal action list — not the engine
handle. `EpisodeRunner` orchestrates observe → act → step. Full board state
(`engine.state`) returns an immutable `BoardSnapshot` for logging and tests only.
`Observation` and `BoardSnapshot` use read-only mappings — see
[design.md §3.4](design.md#34-value-objects-dataclasses) for immutability details.

Turn order is always supplied externally; the engine never assumes alternating
A/B play.

See [design.md](design.md) for layer diagrams, failure-mode semantics, win
detection, information boundaries, and extension points.

## Replay formats

**Text** (hand-editing friendly):

```text
n 1
turn A B A
move A lift 1
move B lift 1
move A place 3
```

**JSON** (tooling friendly):

```json
{
  "n": 1,
  "turn_order": ["A", "B", "A"],
  "moves": [
    {"player": "A", "action": "lift 1"},
    {"player": "B", "action": "lift 1"},
    {"player": "A", "action": "place 3"}
  ]
}
```

Replay CLI validates move players against `turn_order` by default (`--no-strict`
to disable).

## Project layout

```
src/hanoi_crossing/
  actions.py        # Action, ActionKind, parsers
  models.py         # BoardState, BoardSnapshot, Observation, StepResult, StepTrace
  engine.py         # HanoiCrossingEngine
  agents.py         # Agent protocol, RandomAgent, ScriptedAgent
  runner.py         # EpisodeRunner, validate_replay
  formatting.py     # Replay I/O, formatting, serialization
  cli/
    replay.py       # Replay CLI
    random_play.py  # Random-play CLI
src/tests/
examples/
design.md           # Architecture and design decisions (detailed)
```

## Development notes

Build order and reversed decisions are documented in [design.md §10](design.md#10-decisions-tried-and-reversed).
This section records the journey for reviewers when commit history is squashed.

### Build order

1. **Types** — `actions.py` + `models.py` before rule logic
2. **Engine** — `HanoiCrossingEngine` with external turn order
3. **Runner + agents** — `EpisodeRunner`, `Agent` protocol, reference policies
4. **CLI** — replay and random-play on top of the public API
5. **Tests** — engine directly; runner, formatting, and CLI smoke tests
6. **design.md** — consolidated architecture and semantics

### Key reversals

| Early idea | Final choice |
|------------|--------------|
| `act(engine, player)` | `act(observation, legal_actions)` — structural info boundary |
| `Game` + monolithic `types.py` | `HanoiCrossingEngine` + `actions` / `models` split |
| Win check for acting player only | Check both players; tie-break to acting player |
| Raise on illegal moves | `valid=False`, advance turn (per brief) |

## AI disclosure

Built with **Cursor AI (Claude)** as a pair-programming assistant: scaffolding,
engine, runner, agents, tests, CLI, and documentation.

## License

MIT (add a LICENSE file if distributing).
