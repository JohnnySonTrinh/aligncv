from __future__ import annotations

import curses
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .storage import LeaderboardStore, ScoreEntry


BOARD_WIDTH = 38
BOARD_HEIGHT = 16
HUD_HEIGHT = 4
INITIAL_SPEED = 0.14
MIN_SPEED = 0.06
MAX_SPEED = 0.24
POWER_UP_DURATION = 45
SCORE_PER_FOOD = 10
SCORE_PER_POWER_UP = 5
NAME_MAX_LENGTH = 12

PAIR_TITLE = 1
PAIR_MENU = 2
PAIR_MENU_SELECTED = 3
PAIR_BORDER = 4
PAIR_GRID_A = 5
PAIR_GRID_B = 6
PAIR_SNAKE_HEAD = 7
PAIR_SNAKE_BODY_A = 8
PAIR_SNAKE_BODY_B = 9
PAIR_FOOD = 10
PAIR_DOUBLE = 11
PAIR_FAST = 12
PAIR_SLOW = 13
PAIR_DANGER = 14
PAIR_WIN = 15
PAIR_INPUT = 16


Point = tuple[int, int]


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def delta(self) -> Point:
        return self.value

    def is_opposite(self, other: "Direction") -> bool:
        dx1, dy1 = self.delta
        dx2, dy2 = other.delta
        return dx1 + dx2 == 0 and dy1 + dy2 == 0


class PowerUpType(Enum):
    DOUBLE_SCORE = "2X"
    FAST = "FAST"
    SLOW = "SLOW"


@dataclass(slots=True)
class ActiveEffect:
    kind: PowerUpType
    turns_left: int


@dataclass(slots=True)
class GameState:
    width: int = BOARD_WIDTH
    height: int = BOARD_HEIGHT
    snake: list[Point] = field(
        default_factory=lambda: [(12, 10), (11, 10), (10, 10)]
    )
    direction: Direction = Direction.RIGHT
    queued_direction: Direction = Direction.RIGHT
    food: Point = (25, 10)
    power_up: tuple[PowerUpType, Point] | None = None
    score: int = 0
    foods_eaten: int = 0
    turns: int = 0
    speed: float = INITIAL_SPEED
    active_effect: ActiveEffect | None = None
    paused: bool = False
    game_over: bool = False
    won: bool = False

    def snake_head(self) -> Point:
        return self.snake[0]


class SnakeGame:
    def __init__(self, stdscr: curses.window, leaderboard_path: Path) -> None:
        self.stdscr = stdscr
        self.random = random.Random()
        self.store = LeaderboardStore(leaderboard_path)
        self.state = GameState()
        self.use_color = False

    def run(self) -> None:
        self.hide_cursor()
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        curses.noecho()
        curses.cbreak()
        self.setup_colors()

        while True:
            choice = self.show_main_menu()
            if choice == "quit":
                return
            if choice == "leaderboard":
                self.show_leaderboard()
                continue
            replay = True
            while replay:
                self.reset_game()
                self.play_game()
                replay = self.handle_game_over()

    def hide_cursor(self) -> None:
        try:
            curses.curs_set(0)
        except curses.error:
            # Some terminals reject cursor visibility changes; the game can still run.
            pass

    def setup_colors(self) -> None:
        if not curses.has_colors():
            return

        try:
            curses.start_color()
            curses.use_default_colors()
        except curses.error:
            return

        palette = [
            (PAIR_TITLE, curses.COLOR_CYAN, -1),
            (PAIR_MENU, curses.COLOR_WHITE, -1),
            (PAIR_MENU_SELECTED, curses.COLOR_BLACK, curses.COLOR_YELLOW),
            (PAIR_BORDER, curses.COLOR_BLUE, -1),
            (PAIR_GRID_A, curses.COLOR_BLUE, -1),
            (PAIR_GRID_B, curses.COLOR_CYAN, -1),
            (PAIR_SNAKE_HEAD, curses.COLOR_GREEN, -1),
            (PAIR_SNAKE_BODY_A, curses.COLOR_YELLOW, -1),
            (PAIR_SNAKE_BODY_B, curses.COLOR_GREEN, -1),
            (PAIR_FOOD, curses.COLOR_RED, -1),
            (PAIR_DOUBLE, curses.COLOR_MAGENTA, -1),
            (PAIR_FAST, curses.COLOR_YELLOW, -1),
            (PAIR_SLOW, curses.COLOR_CYAN, -1),
            (PAIR_DANGER, curses.COLOR_RED, -1),
            (PAIR_WIN, curses.COLOR_GREEN, -1),
            (PAIR_INPUT, curses.COLOR_BLACK, curses.COLOR_GREEN),
        ]

        for pair_id, fg, bg in palette:
            try:
                curses.init_pair(pair_id, fg, bg)
            except curses.error:
                continue

        self.use_color = True

    def reset_game(self) -> None:
        self.state = GameState()
        self.state.food = self.random_open_position()

    def show_main_menu(self) -> str:
        index = 0
        options = [
            ("play", "Start game"),
            ("leaderboard", "View top 5"),
            ("quit", "Exit"),
        ]
        while True:
            self.stdscr.erase()
            title_attr = self.style(
                PAIR_TITLE,
                curses.A_BOLD | (curses.A_BLINK if self.pulse() else curses.A_NORMAL),
            )
            self.center_text(1, "ONE-SHOT SNAKE", title_attr)
            self.center_text(3, "Neon terminal edition", self.style(PAIR_MENU))
            self.center_text(4, "Arrow keys or WASD to move", self.style(PAIR_MENU))
            self.center_text(5, "Power-ups: 2X, FAST, SLOW", self.style(PAIR_MENU))
            for offset, (_, label) in enumerate(options):
                if offset == index:
                    attr = self.style(PAIR_MENU_SELECTED, curses.A_BOLD)
                else:
                    attr = self.style(PAIR_MENU)
                self.center_text(8 + offset, label, attr)
            self.center_text(13, "Press Enter to choose", self.style(PAIR_BORDER))
            self.stdscr.refresh()

            key = self.stdscr.getch()
            if key in (curses.KEY_UP, ord("w"), ord("W")):
                index = (index - 1) % len(options)
            elif key in (curses.KEY_DOWN, ord("s"), ord("S")):
                index = (index + 1) % len(options)
            elif key in (10, 13, curses.KEY_ENTER):
                return options[index][0]
            time.sleep(0.04)

    def show_leaderboard(self) -> None:
        scores = self.store.load()
        while True:
            self.stdscr.erase()
            self.center_text(1, "TOP 5 LEADERBOARD", self.style(PAIR_TITLE, curses.A_BOLD))
            if not scores:
                self.center_text(4, "No scores yet. Be the first run.", self.style(PAIR_MENU))
            else:
                for row, entry in enumerate(scores, start=0):
                    line = (
                        f"{row + 1}. {entry.name:<12} "
                        f"score={entry.score:<4} foods={entry.foods:<3} turns={entry.turns}"
                    )
                    rank_attr = self.style(PAIR_WIN if row == 0 else PAIR_MENU)
                    self.center_text(4 + row, line, rank_attr)
            self.center_text(12, "Press B to go back", self.style(PAIR_BORDER))
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key in (ord("b"), ord("B"), 27, ord("q"), ord("Q")):
                return
            time.sleep(0.04)

    def play_game(self) -> bool:
        while not self.state.game_over:
            frame_start = time.monotonic()
            self.process_input()
            if self.state.paused:
                self.draw(paused=True)
                time.sleep(0.05)
                continue
            self.step()
            self.draw()
            elapsed = time.monotonic() - frame_start
            time.sleep(max(0.0, self.state.speed - elapsed))
        return True

    def process_input(self) -> None:
        key = self.stdscr.getch()
        if key == -1:
            return

        mapping = {
            curses.KEY_UP: Direction.UP,
            curses.KEY_DOWN: Direction.DOWN,
            curses.KEY_LEFT: Direction.LEFT,
            curses.KEY_RIGHT: Direction.RIGHT,
            ord("w"): Direction.UP,
            ord("W"): Direction.UP,
            ord("s"): Direction.DOWN,
            ord("S"): Direction.DOWN,
            ord("a"): Direction.LEFT,
            ord("A"): Direction.LEFT,
            ord("d"): Direction.RIGHT,
            ord("D"): Direction.RIGHT,
        }

        if key in mapping:
            candidate = mapping[key]
            if not candidate.is_opposite(self.state.direction):
                self.state.queued_direction = candidate
            return

        if key in (ord("p"), ord("P")):
            self.state.paused = not self.state.paused
        elif key in (ord("q"), ord("Q")):
            self.state.game_over = True

    def step(self) -> None:
        self.state.direction = self.state.queued_direction
        dx, dy = self.state.direction.delta
        head_x, head_y = self.state.snake_head()
        new_head = (head_x + dx, head_y + dy)
        self.state.turns += 1

        if self.hits_wall(new_head) or new_head in self.state.snake:
            self.state.game_over = True
            return

        self.state.snake.insert(0, new_head)
        grew = False

        if new_head == self.state.food:
            grew = True
            self.state.foods_eaten += 1
            multiplier = 2 if self.effect_is_active(PowerUpType.DOUBLE_SCORE) else 1
            self.state.score += SCORE_PER_FOOD * multiplier
            self.state.food = self.random_open_position()
            if self.state.foods_eaten % 3 == 0 and self.state.power_up is None:
                self.spawn_power_up()

        if self.state.power_up and new_head == self.state.power_up[1]:
            grew = True
            power_kind, _ = self.state.power_up
            self.apply_power_up(power_kind)
            self.state.score += SCORE_PER_POWER_UP
            self.state.power_up = None

        if not grew:
            self.state.snake.pop()

        self.tick_effect()

        if len(self.state.snake) == self.state.width * self.state.height:
            self.state.won = True
            self.state.game_over = True

    def draw(self, paused: bool = False) -> None:
        self.stdscr.erase()
        self.draw_border()
        self.draw_grid()
        self.draw_hud(paused)
        self.draw_entities()
        self.stdscr.refresh()

    def draw_border(self) -> None:
        border_pair = self.effect_pair() or PAIR_BORDER
        horizontal = "=" if self.pulse() else "#"
        for x in range(self.state.width + 2):
            self.safe_addch(
                HUD_HEIGHT,
                x,
                horizontal,
                self.style(border_pair, curses.A_BOLD),
            )
            self.safe_addch(
                HUD_HEIGHT + self.state.height + 1,
                x,
                horizontal,
                self.style(border_pair, curses.A_BOLD),
            )
        for y in range(self.state.height):
            self.safe_addch(
                HUD_HEIGHT + y + 1,
                0,
                "|",
                self.style(border_pair, curses.A_BOLD),
            )
            self.safe_addch(
                HUD_HEIGHT + y + 1,
                self.state.width + 1,
                "|",
                self.style(border_pair, curses.A_BOLD),
            )

    def draw_grid(self) -> None:
        for y in range(self.state.height):
            for x in range(self.state.width):
                glyph = "." if (x + y + self.state.turns) % 2 == 0 else ":"
                pair = PAIR_GRID_A if (x + y) % 2 == 0 else PAIR_GRID_B
                self.draw_at(x, y, glyph, self.style(pair, curses.A_DIM))

    def draw_hud(self, paused: bool) -> None:
        effect_text = "NONE"
        effect_attr = self.style(PAIR_MENU)
        if self.state.active_effect:
            effect_text = (
                f"{self.state.active_effect.kind.value}:{self.state.active_effect.turns_left}"
            )
            effect_attr = self.style(
                self.effect_pair() or PAIR_MENU,
                curses.A_BOLD if self.pulse() else curses.A_NORMAL,
            )
        drop_text = "--"
        drop_attr = self.style(PAIR_MENU)
        if self.state.power_up:
            kind, _ = self.state.power_up
            drop_text = kind.value
            drop_attr = self.style(self.power_pair(kind), curses.A_BOLD)
        lines = [
            "ONE-SHOT SNAKE [PAUSED]" if paused else "ONE-SHOT SNAKE",
            f"SC:{self.state.score:<4} FD:{self.state.foods_eaten:<2} SP:{self.state.speed:.2f}",
            f"FX:{effect_text:<8} DROP:{drop_text:<4}",
            "MOVE: arrows/WASD   P pause   Q quit",
        ]
        title_pair = PAIR_FAST if paused else (self.effect_pair() or PAIR_TITLE)
        self.safe_addstr(
            0,
            0,
            lines[0][: self.state.width + 2],
            self.style(title_pair, curses.A_BOLD),
        )
        self.safe_addstr(1, 0, lines[1][: self.state.width + 2], self.style(PAIR_MENU))
        self.safe_addstr(2, 0, lines[2][: self.state.width + 2], self.style(PAIR_MENU))
        self.safe_addstr(2, 3, effect_text[:8], effect_attr)
        drop_col = min(self.state.width + 1, len("FX:" + effect_text.ljust(8) + " DROP:"))
        self.safe_addstr(2, drop_col, drop_text[:4], drop_attr)
        self.safe_addstr(3, 0, lines[3][: self.state.width + 2], self.style(PAIR_BORDER))

    def draw_entities(self) -> None:
        food_x, food_y = self.state.food
        food_pair = PAIR_DOUBLE if self.effect_is_active(PowerUpType.DOUBLE_SCORE) else PAIR_FOOD
        food_attr = self.style(food_pair, curses.A_BOLD if self.pulse() else curses.A_NORMAL)
        self.draw_at(food_x, food_y, "*", food_attr)

        if self.state.power_up:
            kind, (power_x, power_y) = self.state.power_up
            glyph = {PowerUpType.DOUBLE_SCORE: "2", PowerUpType.FAST: ">", PowerUpType.SLOW: "<"}[kind]
            self.draw_at(
                power_x,
                power_y,
                glyph,
                self.style(self.power_pair(kind), curses.A_BOLD),
            )

        for index, (x, y) in enumerate(self.state.snake):
            if index == 0:
                glyph = "@"
                pair = self.effect_pair() or PAIR_SNAKE_HEAD
                attr = self.style(pair, curses.A_BOLD)
            else:
                glyph = "o"
                pair = PAIR_SNAKE_BODY_A if index % 2 == 0 else PAIR_SNAKE_BODY_B
                if self.state.active_effect and index % 3 == 0:
                    pair = self.effect_pair() or pair
                attr = self.style(pair)
            self.draw_at(x, y, glyph, attr)

    def handle_game_over(self) -> bool:
        leaderboard = self.store.load()
        qualifies = len(leaderboard) < 5 or any(
            self.state.score > entry.score for entry in leaderboard
        )
        if qualifies and self.state.score > 0:
            name = self.prompt_for_name()
            if name:
                leaderboard = self.store.save_score(
                    ScoreEntry(
                        name=name,
                        score=self.state.score,
                        turns=self.state.turns,
                        foods=self.state.foods_eaten,
                    )
                )

        while True:
            self.stdscr.erase()
            title = "YOU WIN" if self.state.won else "GAME OVER"
            title_pair = PAIR_WIN if self.state.won else PAIR_DANGER
            self.center_text(2, title, self.style(title_pair, curses.A_BOLD))
            self.center_text(4, f"Final score: {self.state.score}", self.style(PAIR_MENU))
            self.center_text(5, f"Foods eaten: {self.state.foods_eaten}", self.style(PAIR_MENU))
            self.center_text(6, f"Turns survived: {self.state.turns}", self.style(PAIR_MENU))
            if qualifies and self.state.score > 0:
                self.center_text(8, "Leaderboard updated", self.style(PAIR_WIN, curses.A_BOLD))
            self.center_text(10, "Press R to replay or M for menu", self.style(PAIR_BORDER))
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key in (ord("r"), ord("R")):
                return True
            if key in (ord("m"), ord("M"), 27):
                return False
            time.sleep(0.05)

    def prompt_for_name(self) -> str:
        buffer: list[str] = []
        while True:
            self.stdscr.erase()
            self.center_text(3, "New high score!", self.style(PAIR_WIN, curses.A_BOLD))
            self.center_text(5, "Enter your name and press Enter", self.style(PAIR_MENU))
            self.center_text(6, "(letters, numbers, dash, underscore)", self.style(PAIR_BORDER))
            self.center_text(8, "".join(buffer) or "_", self.style(PAIR_INPUT, curses.A_BOLD))
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key in (10, 13, curses.KEY_ENTER):
                value = "".join(buffer).strip().upper()
                return value[:NAME_MAX_LENGTH] or "PLAYER"
            if key in (curses.KEY_BACKSPACE, 127, 8):
                if buffer:
                    buffer.pop()
                continue
            if 32 <= key <= 126 and len(buffer) < NAME_MAX_LENGTH:
                char = chr(key)
                if char.isalnum() or char in "-_ ":
                    buffer.append(char)

    def draw_at(self, x: int, y: int, glyph: str, attr: int = curses.A_NORMAL) -> None:
        self.safe_addch(HUD_HEIGHT + y + 1, x + 1, glyph, attr)

    def center_text(self, row: int, text: str, attr: int = curses.A_NORMAL) -> None:
        max_y, max_x = self.stdscr.getmaxyx()
        col = max(0, (max_x - len(text)) // 2)
        self.safe_addstr(min(row, max_y - 1), col, text[: max_x - col], attr)

    def safe_addstr(self, row: int, col: int, text: str, attr: int = curses.A_NORMAL) -> None:
        try:
            self.stdscr.addstr(row, col, text, attr)
        except curses.error:
            return

    def safe_addch(self, row: int, col: int, glyph: str, attr: int = curses.A_NORMAL) -> None:
        try:
            self.stdscr.addch(row, col, glyph, attr)
        except curses.error:
            return

    def style(self, pair_id: int, attrs: int = curses.A_NORMAL) -> int:
        attr = attrs
        if self.use_color:
            attr |= curses.color_pair(pair_id)
        return attr

    def pulse(self) -> bool:
        return int(time.monotonic() * 6) % 2 == 0

    def power_pair(self, kind: PowerUpType) -> int:
        if kind == PowerUpType.DOUBLE_SCORE:
            return PAIR_DOUBLE
        if kind == PowerUpType.FAST:
            return PAIR_FAST
        return PAIR_SLOW

    def effect_pair(self) -> int | None:
        if self.state.active_effect is None:
            return None
        return self.power_pair(self.state.active_effect.kind)

    def hits_wall(self, point: Point) -> bool:
        x, y = point
        return x < 0 or y < 0 or x >= self.state.width or y >= self.state.height

    def random_open_position(self) -> Point:
        occupied = set(self.state.snake)
        if self.state.power_up:
            occupied.add(self.state.power_up[1])
        occupied.add(self.state.food)
        available = [
            (x, y)
            for x in range(self.state.width)
            for y in range(self.state.height)
            if (x, y) not in occupied
        ]
        if not available:
            return (0, 0)
        return self.random.choice(available)

    def spawn_power_up(self) -> None:
        kind = self.random.choice(list(PowerUpType))
        self.state.power_up = (kind, self.random_open_position())

    def apply_power_up(self, kind: PowerUpType) -> None:
        if kind == PowerUpType.FAST:
            self.state.speed = max(MIN_SPEED, self.state.speed - 0.03)
        elif kind == PowerUpType.SLOW:
            self.state.speed = min(MAX_SPEED, self.state.speed + 0.03)
        self.state.active_effect = ActiveEffect(kind=kind, turns_left=POWER_UP_DURATION)

    def effect_is_active(self, kind: PowerUpType) -> bool:
        return self.state.active_effect is not None and self.state.active_effect.kind == kind

    def tick_effect(self) -> None:
        effect = self.state.active_effect
        if effect is None:
            return
        effect.turns_left -= 1
        if effect.turns_left > 0:
            return
        if effect.kind == PowerUpType.FAST:
            self.state.speed = min(MAX_SPEED, self.state.speed + 0.03)
        elif effect.kind == PowerUpType.SLOW:
            self.state.speed = max(MIN_SPEED, self.state.speed - 0.03)
        self.state.active_effect = None


def run_game(stdscr: curses.window, leaderboard_path: Path) -> None:
    min_height = HUD_HEIGHT + BOARD_HEIGHT + 3
    min_width = BOARD_WIDTH + 2
    height, width = stdscr.getmaxyx()
    if height < min_height or width < min_width:
        raise RuntimeError(
            f"Terminal too small. Need at least {min_width}x{min_height}, got {width}x{height}."
        )
    SnakeGame(stdscr, leaderboard_path).run()
