# Learning Log

## What I learned while one-shotting this project

- A terminal game stays much safer and cleaner when `curses.wrapper(...)` owns setup and teardown, because it restores terminal state even if the game exits unexpectedly.
- Keeping the leaderboard in a tiny JSON file is enough for a local terminal game, as long as the loader tolerates missing or malformed data.
- `curses` input loops feel better when rendering and sleeping are frame-based instead of blocking on keyboard input.
- Speed-changing power-ups are easier to reason about when the game stores speed as frame delay seconds and clamps that value inside a min/max range.
- Small menus and HUD text need explicit terminal-size checks up front, otherwise `curses` drawing can fail in cramped terminal windows.
- Designing for a normal `80x24` terminal matters more than building for a larger dev window, because a terminal game should feel ready-to-run in default shell sizes.
- Terminal color work is best done with safe fallbacks, because `curses` color support and blink behavior vary a lot across emulators.

## Tradeoffs made

- I used only the Python standard library so the project stays easy to run and audit.
- I chose a persistent top-five leaderboard instead of a more complex profile system to keep the one-shot focused and maintainable.
- I kept the power-up system intentionally small but extensible, so new effects can be added later without rewriting the main game loop.
