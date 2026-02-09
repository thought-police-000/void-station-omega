"""Mutable game state: flags, counters, score, turn tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from engine.types import Timer


@dataclass
class GameState:
    current_room: str = ""
    score: int = 0
    turns: int = 0
    max_score: int = 0
    flags: dict[str, bool] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)
    visited: set[str] = field(default_factory=set)
    timers: dict[str, Timer] = field(default_factory=dict)
    game_over: bool = False
    won: bool = False

    # --- flags ---

    def set_flag(self, name: str) -> None:
        self.flags[name] = True

    def clear_flag(self, name: str) -> None:
        self.flags[name] = False

    def flag_is_set(self, name: str) -> bool:
        return self.flags.get(name, False)

    # --- counters ---

    def get_counter(self, name: str) -> int:
        return self.counters.get(name, 0)

    def set_counter(self, name: str, value: int) -> None:
        self.counters[name] = value

    def inc_counter(self, name: str, amount: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + amount

    def dec_counter(self, name: str, amount: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) - amount

    # --- room tracking ---

    def enter_room(self, room_id: str) -> bool:
        """Move to room, return True if first visit."""
        self.current_room = room_id
        first = room_id not in self.visited
        self.visited.add(room_id)
        return first

    # --- score ---

    def add_score(self, points: int) -> None:
        self.score += points

    # --- timers ---

    def register_timer(self, timer: Timer) -> None:
        self.timers[timer.name] = timer

    def enable_timer(self, name: str) -> None:
        if name in self.timers:
            self.timers[name].active = True

    def disable_timer(self, name: str) -> None:
        if name in self.timers:
            self.timers[name].active = False

    def tick_timers(self) -> list[tuple[str, int, str]]:
        """Advance all active timers. Returns list of (name, value, message)
        for timers that ticked, plus any that hit zero."""
        results: list[tuple[str, int, str]] = []
        for timer in self.timers.values():
            if not timer.active:
                continue
            self.dec_counter(timer.counter)
            val = self.get_counter(timer.counter)
            msg = ""
            if timer.message_template and val > 0:
                msg = timer.message_template.replace("{value}", str(val))
            results.append((timer.name, val, msg))
        return results

    # --- serialization helpers ---

    def to_dict(self) -> dict:
        return {
            "current_room": self.current_room,
            "score": self.score,
            "turns": self.turns,
            "flags": dict(self.flags),
            "counters": dict(self.counters),
            "visited": list(self.visited),
            "active_timers": [n for n, t in self.timers.items() if t.active],
            "game_over": self.game_over,
            "won": self.won,
        }

    def load_dict(self, data: dict) -> None:
        self.current_room = data["current_room"]
        self.score = data["score"]
        self.turns = data["turns"]
        self.flags = data["flags"]
        self.counters = data["counters"]
        self.visited = set(data["visited"])
        self.game_over = data.get("game_over", False)
        self.won = data.get("won", False)
        for name in data.get("active_timers", []):
            if name in self.timers:
                self.timers[name].active = True
