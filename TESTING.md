# Testing Notes

## Checks Run

```bash
python3 -m compileall src
PYTHONPATH=src python3 -m snake_game
```

## Manual Test Checklist

- Launch the game in a terminal large enough for the board
- Confirm menu navigation works with arrow keys
- Start a run and verify movement with both arrows and `WASD`
- Eat food and confirm score increases
- Reach every third food and confirm a power-up can spawn
- Collect `2X` and verify food awards double points while active
- Collect `FAST` and `SLOW` and verify speed changes temporarily
- Crash into a wall or the snake body and verify game-over handling
- Enter a high-score name and verify it persists in `snake_leaderboard.json`
- Re-open the game and verify the top-five leaderboard remains available

## Notes

- Interactive `curses` gameplay is best validated manually in a real terminal session.
- The shipped layout was adjusted to fit a standard `80x24` terminal.
- The color system is designed to fall back gracefully if the terminal does not expose full color support.
- Automated unit tests were intentionally kept out of this one-shot so the shipping path stays simple and dependency-free.
