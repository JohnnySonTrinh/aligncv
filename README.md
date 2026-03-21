# One-Shot Snake Game

Terminal-first Snake built with Python and the standard library.

## Features

- `curses`-based gameplay inside the terminal
- Colorful arcade-style HUD, menu, and board accents
- Persistent top-5 leaderboard stored in `snake_leaderboard.json`
- Power-ups:
  - `2X` doubles food score for a limited time
  - `FAST` temporarily increases game speed
  - `SLOW` temporarily decreases game speed
- Menu flow for play, leaderboard, replay, and quit
- Safe terminal handling through `curses.wrapper(...)`

## Requirements

- Python `3.11+`
- A terminal with `curses` support

## Run

```bash
PYTHONPATH=src python3 -m snake_game
```

Or install it locally and use the script:

```bash
python3 -m pip install -e .
snake-game
```

## Controls

- Arrow keys or `WASD`: move
- `P`: pause
- `Q`: end the current run
- `Enter`: confirm menu selections

## Game Notes

- Food is shown as `*`
- Power-ups are color-coded and shown as `2`, `>`, or `<`
- Snake head is `@`, body is `o`
- Every third food can spawn a power-up

## Leaderboard

The game stores the top five scores in `snake_leaderboard.json` in the project root. If the file is missing or corrupted, the game safely falls back to an empty leaderboard.
