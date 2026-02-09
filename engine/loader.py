"""Load game data from JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from engine.types import (
    Action, ActionType, Condition, ConditionType, Direction, Event, Exit,
    Item, Manifest, Timer, Vocabulary,
)
from engine.world import Room


def _load_json(path: Path) -> dict | list:
    with open(path) as f:
        return json.load(f)


def _parse_direction(s: str) -> Direction:
    return Direction(s.lower())


def _parse_exit(data: dict) -> Exit:
    return Exit(
        direction=_parse_direction(data["direction"]),
        destination=data["destination"],
        locked=data.get("locked", False),
        lock_flag=data.get("lock_flag"),
        lock_message=data.get("lock_message", "The way is blocked."),
    )


def _parse_room(data: dict) -> Room:
    return Room(
        id=data["id"],
        name=data["name"],
        description=data["description"],
        exits=[_parse_exit(e) for e in data.get("exits", [])],
        dark=data.get("dark", False),
        dark_description=data.get("dark_description",
                                  "It's pitch black. You can't see a thing."),
        first_visit_text=data.get("first_visit_text"),
        visit_flag=data.get("visit_flag"),
    )


def _parse_item(data: dict) -> Item:
    return Item(
        id=data["id"],
        name=data["name"],
        description=data["description"],
        room_description=data.get("room_description", ""),
        location=data.get("location", "__nowhere__"),
        takeable=data.get("takeable", True),
        weight=data.get("weight", 1),
        aliases=data.get("aliases", []),
        combine_with=data.get("combine_with"),
        combine_result=data.get("combine_result"),
        combine_message=data.get("combine_message"),
    )


def _parse_condition(data: dict) -> Condition:
    return Condition(
        type=ConditionType(data["type"]),
        target=data["target"],
        value=data.get("value"),
    )


def _parse_action(data: dict) -> Action:
    return Action(
        type=ActionType(data["type"]),
        target=data.get("target", ""),
        value=data.get("value"),
    )


def _parse_event(data: dict) -> Event:
    return Event(
        id=data["id"],
        verb=data.get("verb"),
        noun=data.get("noun"),
        room=data.get("room"),
        conditions=[_parse_condition(c) for c in data.get("conditions", [])],
        actions=[_parse_action(a) for a in data.get("actions", [])],
        override_builtin=data.get("override_builtin", True),
        once=data.get("once", False),
        priority=data.get("priority", 0),
    )


def _parse_timer(data: dict) -> Timer:
    return Timer(
        name=data["name"],
        counter=data["counter"],
        interval=data.get("interval", 1),
        on_zero_event=data.get("on_zero_event", ""),
        message_template=data.get("message_template", ""),
        active=data.get("active", False),
    )


def load_manifest(data_dir: Path) -> Manifest:
    data = _load_json(data_dir / "manifest.json")
    return Manifest(
        title=data.get("title", "Untitled Adventure"),
        author=data.get("author", "Unknown"),
        version=data.get("version", "1.0"),
        max_score=data.get("max_score", 0),
        max_inventory=data.get("max_inventory", 10),
        start_room=data["start_room"],
        intro_file=data.get("intro_file", "intro.txt"),
        help_file=data.get("help_file", "help.txt"),
    )


def load_rooms(data_dir: Path) -> list[Room]:
    data = _load_json(data_dir / "rooms.json")
    return [_parse_room(r) for r in data]


def load_items(data_dir: Path) -> list[Item]:
    data = _load_json(data_dir / "items.json")
    return [_parse_item(i) for i in data]


def load_events(data_dir: Path) -> tuple[list[Event], list[Timer]]:
    data = _load_json(data_dir / "events.json")
    events = [_parse_event(e) for e in data.get("events", [])]
    timers = [_parse_timer(t) for t in data.get("timers", [])]
    return events, timers


def load_vocabulary(data_dir: Path) -> Vocabulary:
    data = _load_json(data_dir / "vocabulary.json")
    return Vocabulary(
        verb_synonyms=data.get("verb_synonyms", {}),
        noun_synonyms=data.get("noun_synonyms", {}),
        direction_synonyms=data.get("direction_synonyms", {}),
    )


def load_text_file(data_dir: Path, filename: str) -> str:
    path = data_dir / filename
    if path.exists():
        return path.read_text()
    return ""


def validate_world(rooms: list[Room], items: list[Item],
                    events: list[Event]) -> list[str]:
    """Return list of validation errors (empty = OK)."""
    errors: list[str] = []
    room_ids = {r.id for r in rooms}
    item_ids = {i.id for i in items}

    for room in rooms:
        for ex in room.exits:
            if ex.destination not in room_ids:
                errors.append(
                    f"Room '{room.id}' exit {ex.direction.value} -> "
                    f"unknown room '{ex.destination}'")

    for item in items:
        loc = item.location
        if loc not in room_ids and loc not in ("__inventory__", "__nowhere__"):
            errors.append(
                f"Item '{item.id}' has unknown location '{loc}'")

    for event in events:
        if event.room and event.room not in room_ids:
            errors.append(
                f"Event '{event.id}' references unknown room '{event.room}'")

    return errors
