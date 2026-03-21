from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


MAX_LEADERBOARD_ENTRIES = 5


@dataclass(slots=True)
class ScoreEntry:
    name: str
    score: int
    turns: int
    foods: int


class LeaderboardStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> list[ScoreEntry]:
        if not self.path.exists():
            return []

        try:
            raw_entries = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

        results: list[ScoreEntry] = []
        for item in raw_entries:
            try:
                results.append(
                    ScoreEntry(
                        name=str(item["name"])[:12] or "PLAYER",
                        score=max(0, int(item["score"])),
                        turns=max(0, int(item["turns"])),
                        foods=max(0, int(item["foods"])),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue

        return sorted(results, key=lambda entry: entry.score, reverse=True)[
            :MAX_LEADERBOARD_ENTRIES
        ]

    def save_score(self, entry: ScoreEntry) -> list[ScoreEntry]:
        leaderboard = self.load()
        leaderboard.append(entry)
        leaderboard = sorted(leaderboard, key=lambda current: current.score, reverse=True)[
            :MAX_LEADERBOARD_ENTRIES
        ]

        self.path.write_text(
            json.dumps([asdict(item) for item in leaderboard], indent=2),
            encoding="utf-8",
        )
        return leaderboard

