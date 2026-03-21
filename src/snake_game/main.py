from __future__ import annotations

import curses
import sys
from pathlib import Path

from .game import run_game


def leaderboard_file() -> Path:
    return Path.cwd() / "snake_leaderboard.json"


def main() -> int:
    try:
        curses.wrapper(run_game, leaderboard_file())
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
