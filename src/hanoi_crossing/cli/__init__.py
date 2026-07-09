"""CLI entry point — dispatches to replay and random-play modules."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print("usage: hanoi-crossing replay <file> [options]")
        print("       hanoi-crossing random <n> [options]")
        print()
        print("Run 'hanoi-crossing replay --help' or 'hanoi-crossing random --help' for details.")
        return 0 if not args else 1

    command = args[0]
    rest = args[1:]

    if command == "replay":
        from hanoi_crossing.cli.replay import main as replay_main

        return replay_main(rest)
    if command == "random":
        from hanoi_crossing.cli.random_play import main as random_main

        return random_main(rest)

    print(f"error: unknown command {command!r} (expected 'replay' or 'random')", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
