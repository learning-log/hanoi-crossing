# Hanoi Crossing

Two-player Tower of Hanoi variant with a shared middle pole. Each player has
three poles; pole 2 is shared and visible to both. Players start with `N` disks
on their pole 1 (A: odd sizes, B: even sizes) and win by moving all their disks
to pole 3 with an empty hand while poles 1 and 2 are clear.

## Quick start

```bash
uv sync --dev
uv run pytest
uv run hanoi-crossing replay examples/n1_win.txt
uv run hanoi-crossing random --n 2 --turns 100 --seed 1
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

Players never observe the opponent's private poles (`1b`/`3b` for A, `1a`/`3a`
for B) or the opponent's hand.

## Design decisions

### Engine API (RL / service ready)

The `Game` class is the environment core. External agents (random player, RL
policy, online service) interact only through:

| Method | Purpose |
|--------|---------|
| `legal_actions()` | action mask for the current player |
| `step(action)` | apply one turn; illegal moves waste the turn |
| `observation(player)` | player-local partial view |
| `snapshot()` | full state for logging / replay output |
| `clone()` | copy for search or rollout |

Turn order is **always supplied externally** — the engine never assumes
alternating A/B play.

### Pole numbering

Actions use **local pole numbers 1–3** from the acting player's perspective.
Internally poles are keyed `1a`, `2`, `3a`, `1b`, `3b`.

### Illegal moves

An illegal action leaves state unchanged and still consumes the turn, per the
brief. `step()` returns `StepResult(legal=False, ...)`.

### Win detection

After every **legal** state-changing action, the engine checks both players.
A player wins when their hand is empty and, among their visible poles, only
pole 3 holds disks (poles 1 and 2 must be empty).

### Replay formats

**JSON** (good for tooling):

```json
{
  "n": 1,
  "turn_order": ["A", "B", "A"],
  "moves": [
    {"action": "lift", "pole": 1},
    {"action": "lift", "pole": 1},
    {"action": "place", "pole": 3}
  ]
}
```

**Text** (good for hand-editing):

```
n 1
turn A B A
A lift 1
B lift 1
A place 3
```

`moves` align positionally with `turn_order`. Text format additionally prefixes
each move line with the acting player for readability; the CLI verifies it
matches `turn_order`.

### Random play

`hanoi-crossing random` builds a turn sequence (default alternating `AB`), then
each turn samples uniformly from `legal_actions()`. This uses the same API an
external agent would — no engine shortcuts.

## Project layout

```
src/hanoi_crossing/
  types.py    # Player, Action, pole maps
  engine.py   # Game rules and stepping
  cli.py      # replay + random frontends
tests/
examples/
```

Core engine (`engine.py` + `types.py`) is under 200 lines.

## Development notes

This section records **build order and reversed decisions** so the reasoning is
visible even when commit history is imperfect.

### Build order

1. **Types first** (`Player`, `Action`, `POLE_MAP`) — settled naming before any
   rule logic so CLI and tests could share one vocabulary.
2. **Engine** — initial stacks, `legal_actions`, `step`, win check, `observation`
   and `clone` for future RL use.
3. **CLI** — replay parser (JSON + text), then random self-play on top of the
   public engine API.
4. **Tests** — engine rules directly; CLI only for file replay smoke tests.
5. **Examples + README** — documented formats after the parsers existed.

### Decisions tried and reversed

| Early idea | What changed | Why |
|------------|--------------|-----|
| Single global pole list indexed 0–4 | Per-player local poles 1–3 + internal string IDs | Matches the brief's player-centric view; keeps observations natural for agents. |
| Raise on illegal moves | Return `legal=False`, advance turn | Brief says illegal actions waste the turn without changing state. |
| Embed alternating A/B turn logic in `Game` | Turn order passed in at construction | Brief requires external turn sequences (RL schedulers, replay files). |
| Rich text format with implicit turn order | Explicit `turn` line + optional per-move player prefix | Easier to validate replays; catches mismatched recordings early. |
| Check win only for the acting player | Check both players after each legal move | Opponent could already satisfy win before their next explicit turn (edge case; cheap to scan). |

### What I'd do with more time

- Step log with action legality for replay debugging
- Property-based tests for invariants (disk conservation, monotonic stacks)
- Separate `Agent` protocol and a minimal greedy solver as a third frontend

## AI disclosure

This submission was built with **Cursor AI (Claude)** as a pair-programming
assistant: scaffolding the `uv` project, drafting the engine and CLI,
writing tests, and editing this README. Decisions in the tables above were
reviewed and adjusted during that session (e.g. illegal-move semantics, turn
order ownership).

## License

MIT (add a LICENSE file if distributing).
