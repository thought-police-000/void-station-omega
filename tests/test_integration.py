"""Integration tests: full walkthrough and data validation."""

import pytest
from pathlib import Path

from engine.loader import (
    load_manifest, load_rooms, load_items, load_events,
    load_vocabulary, validate_world,
)
from main import run

DATA_DIR = Path(__file__).parent.parent / "game_data"


def _make_input_fn(commands):
    """Create an input function that feeds commands then quits."""
    it = iter(commands)
    def input_fn(prompt=""):
        try:
            return next(it)
        except StopIteration:
            return "quit"
    return input_fn


class TestDataValidation:
    """Validate game data integrity."""

    def test_load_all_data(self):
        manifest = load_manifest(DATA_DIR)
        rooms = load_rooms(DATA_DIR)
        items = load_items(DATA_DIR)
        events, timers = load_events(DATA_DIR)
        vocab = load_vocabulary(DATA_DIR)

        assert manifest.title == "Void Station Omega"
        assert manifest.max_score == 250
        assert len(rooms) >= 25
        assert len(items) >= 10
        assert len(events) >= 20

    def test_validation_passes(self):
        rooms = load_rooms(DATA_DIR)
        items = load_items(DATA_DIR)
        events, _ = load_events(DATA_DIR)
        errors = validate_world(rooms, items, events)
        assert errors == [], f"Validation errors: {errors}"

    def test_start_room_exists(self):
        manifest = load_manifest(DATA_DIR)
        rooms = load_rooms(DATA_DIR)
        room_ids = {r.id for r in rooms}
        assert manifest.start_room in room_ids

    def test_all_exits_bidirectional(self):
        """Check that most exits have a return path (not strict)."""
        rooms = load_rooms(DATA_DIR)
        room_map = {r.id: r for r in rooms}
        warnings = []
        for room in rooms:
            for ex in room.exits:
                dest = room_map.get(ex.destination)
                if dest is None:
                    continue
                has_return = any(
                    ret_ex.destination == room.id for ret_ex in dest.exits
                )
                if not has_return:
                    warnings.append(
                        f"{room.id} -> {dest.id} ({ex.direction.value}) "
                        f"has no return path"
                    )
        # Allow some one-way exits but flag for review
        assert len(warnings) < 5, f"One-way exits: {warnings}"

    def test_all_items_have_valid_locations(self):
        rooms = load_rooms(DATA_DIR)
        items = load_items(DATA_DIR)
        room_ids = {r.id for r in rooms}
        for item in items:
            assert (item.location in room_ids or
                    item.location in ("__inventory__", "__nowhere__")), \
                f"Item '{item.id}' has invalid location '{item.location}'"

    def test_no_orphan_rooms(self):
        """Every room (except start) should be reachable via at least one exit."""
        manifest = load_manifest(DATA_DIR)
        rooms = load_rooms(DATA_DIR)
        destinations = set()
        for room in rooms:
            for ex in room.exits:
                destinations.add(ex.destination)
        room_ids = {r.id for r in rooms}
        orphans = room_ids - destinations - {manifest.start_room}
        assert orphans == set(), f"Orphan rooms: {orphans}"

    def test_score_adds_to_max(self):
        """Verify total available score equals max_score (excluding duplicates)."""
        manifest = load_manifest(DATA_DIR)
        events, _ = load_events(DATA_DIR)

        # Exclude combine_adapter_cell (duplicate of combine_cell_adapter)
        total = 0
        skip = {"combine_adapter_cell"}
        for event in events:
            if event.id in skip:
                continue
            for action in event.actions:
                if action.type.value == "add_score":
                    total += int(action.value)

        assert total == manifest.max_score, \
            f"Score total {total} != max_score {manifest.max_score}"

    def test_reachability(self):
        """BFS from start room can reach all rooms (ignoring locks)."""
        manifest = load_manifest(DATA_DIR)
        rooms = load_rooms(DATA_DIR)
        room_map = {r.id: r for r in rooms}

        visited = set()
        queue = [manifest.start_room]
        while queue:
            rid = queue.pop(0)
            if rid in visited:
                continue
            visited.add(rid)
            room = room_map.get(rid)
            if room:
                for ex in room.exits:
                    if ex.destination not in visited:
                        queue.append(ex.destination)

        unreachable = set(room_map.keys()) - visited
        assert unreachable == set(), f"Unreachable rooms: {unreachable}"


class TestGameplay:
    """Test actual gameplay sequences."""

    def test_game_starts(self):
        """Game starts without errors and shows Cryo Bay."""
        commands = ["look", "quit"]
        score = run(input_fn=_make_input_fn(commands))
        assert score == 0

    def test_basic_puzzle_chain_1(self):
        """Complete puzzle chain 1: escape starting area."""
        commands = [
            "east",             # -> Medbay
            "take bar",         # +5
            "west",             # -> Cryo Bay
            "use bar",          # +10
            "south",            # -> Corridor
            "take card",        # +10
            "east",             # -> Command Center (+10)
            "quit",
        ]
        score = run(input_fn=_make_input_fn(commands))
        assert score == 35

    def test_full_walkthrough(self):
        """Complete the entire game with max score = 250."""
        commands = [
            # --- Gather items from Deck A first (no timer pressure) ---
            # Chain 1: Escape Starting Area
            "east",                             # Cryo Bay -> Medbay
            "take bar",                         # +5
            "west",                             # -> Cryo Bay
            "use bar",                          # +10
            "south",                            # -> Deck A Corridor Fore
            "take card",                        # +10 (unlocks Command)
            "east",                             # -> Command Center (+10 auto)
            "examine log",                      # +10 (learn code 7439)
            "north",                            # -> Bridge
            "take chip",                        # +10
            "south",                            # -> Command Center
            "west",                             # -> Deck A Corridor Fore
            "south",                            # -> Deck A Corridor Aft
            "east",                             # -> Security
            "take flashlight",                  # +10
            "use bar",                          # +10 (open locker)
            "take grenade",                     # take EMP (no score)
            "west",                             # -> Deck A Corridor Aft
            # --- Go to Deck B, gather items & do bio puzzle ---
            "down",                             # -> Deck B Corridor Fore
            "east",                             # -> Lab C-1
            "take notes",                       # take (no score)
            "examine notes",                    # +10
            "west",                             # -> Deck B Corridor Fore
            "south",                            # -> Deck B Corridor Aft
            "west",                             # -> Lab C-4
            "take adapter",                     # +5
            "east",                             # -> Deck B Corridor Aft
            "east",                             # -> Lab C-3
            "take cell",                        # +5
            "combine cell with adapter",        # +10
            "west",                             # -> Deck B Corridor Aft
            # Go to Deck C, install reactor, get suit
            "down",                             # -> Deck C Corridor
            "east",                             # -> Reactor Room
            "use powered cell",                 # +10 (reactor powered)
            "west",                             # -> Deck C Corridor
            "west",                             # -> Life Support
            "take suit",                        # +10
            "east",                             # -> Deck C Corridor
            # Set up terminal
            "use chip",                         # +10 (repair terminal)
            "use terminal",                     # +15 (enter code 7439)
            # Navigate shaft (for score)
            "down",                             # -> Maintenance Shaft (+10 navigate)
            "up",                               # -> Deck C Corridor
            # Go back to Deck B to get artifact (starts timer)
            "up",                               # -> Deck B Corridor Aft
            "north",                            # -> Deck B Corridor Fore
            "west",                             # -> Lab C-2
            "take badge",                       # +10
            "use badge",                        # +15 (open bio lock)
            "south",                            # -> Alien Chamber
            "take artifact",                    # +20 (starts 15-turn self-destruct)
            # --- TIMER STARTS: 15 turns ---
            "north",                            # -> Lab C-2            (14)
            "east",                             # -> Deck B Corridor 1  (13)
            "south",                            # -> Deck B Corridor 2  (12)
            "down",                             # -> Deck C Corridor    (11)
            "use grenade",                      # +10 stun alien        (10)
            "north",                            # -> Escape Pod Bay     (9)
            "use artifact",                     # +15 power pod         (8)
            "use pod",                          # +20 LAUNCH! WIN!
        ]
        score = run(input_fn=_make_input_fn(commands))
        assert score == 250
