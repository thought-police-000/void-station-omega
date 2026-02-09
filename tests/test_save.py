"""Tests for save/load system."""

import json
import os
import pytest
from engine.save import save_game, load_game
from engine.game_state import GameState
from engine.types import Item, ItemLocation, Room
from engine.world import World


@pytest.fixture
def setup(tmp_path):
    rooms = [Room(id="room1", name="Room 1", description="A room.")]
    items = [
        Item(id="key", name="key", description="A key.",
             room_description="A key.",
             location=ItemLocation.INVENTORY.value),
        Item(id="sword", name="sword", description="A sword.",
             room_description="A sword.", location="room1"),
    ]
    world = World(rooms, items)
    state = GameState(current_room="room1", score=42, turns=10, max_score=100)
    state.set_flag("door_open")
    state.set_counter("health", 7)
    state.visited.add("room1")
    save_path = str(tmp_path / "test_save.json")
    return state, world, save_path


def test_save_creates_file(setup):
    state, world, path = setup
    msg = save_game(state, world, path)
    assert "saved" in msg.lower()
    assert os.path.exists(path)


def test_save_load_roundtrip(setup):
    state, world, path = setup
    save_game(state, world, path)

    # Create fresh state and world with reset values
    rooms = [Room(id="room1", name="Room 1", description="A room.")]
    items = [
        Item(id="key", name="key", description="A key.",
             room_description="A key.", location="room1"),
        Item(id="sword", name="sword", description="A sword.",
             room_description="A sword.", location="room1"),
    ]
    new_world = World(rooms, items)
    new_state = GameState(max_score=100)

    msg = load_game(new_state, new_world, path)
    assert "loaded" in msg.lower()

    assert new_state.current_room == "room1"
    assert new_state.score == 42
    assert new_state.turns == 10
    assert new_state.flag_is_set("door_open")
    assert new_state.get_counter("health") == 7
    assert "room1" in new_state.visited

    # Check item locations restored
    assert new_world.get_item("key").location == ItemLocation.INVENTORY.value
    assert new_world.get_item("sword").location == "room1"


def test_load_no_file(setup):
    _, world, _ = setup
    state = GameState()
    msg = load_game(state, world, "/nonexistent/path.json")
    assert "no save" in msg.lower()


def test_save_format(setup):
    state, world, path = setup
    save_game(state, world, path)
    with open(path) as f:
        data = json.load(f)
    assert "state" in data
    assert "item_locations" in data
    assert data["state"]["score"] == 42
    assert data["item_locations"]["key"] == ItemLocation.INVENTORY.value
