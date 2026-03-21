# Debug Log

## Debugging and fixes captured during the build

- I guarded leaderboard loading against file corruption and partial JSON data so a broken score file does not crash the game.
- I added a terminal-size check before the game starts because `curses` drawing calls can throw errors when the terminal is too small.
- I clamped speed adjustments for `FAST` and `SLOW` power-ups so stacked effects cannot push the frame delay into an unusable range.
- I kept name input filtered to printable safe characters to avoid odd control-character behavior inside the `curses` prompt.
- During smoke testing, the first board layout was too tall for a standard `80x24` terminal, so I resized the default board and HUD to make startup work in a more typical shell window.
- I added guarded color initialization so the game can still run cleanly even if a terminal exposes limited or inconsistent `curses` color capabilities.
