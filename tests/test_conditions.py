"""Tests for condition evaluator."""

import pytest
from engine.conditions import evaluate, evaluate_all
from engine.types import Condition, ConditionType, Item, ItemLocation, Room
from engine.game_state import GameState
from engine.world import World


@pytest.fixture
def setup():
    rooms = [Room(id="room1", name="Room 1", description="A room.")]
    items = [
        Item(id="key", name="key", description="A key.",
             room_description="A key.", location="room1"),
        Item(id="sword", name="sword", description="A sword.",
             room_description="A sword.",
             location=ItemLocation.INVENTORY.value),
        Item(id="ghost", name="ghost", description="Gone.",
             room_description="", location=ItemLocation.NOWHERE.value),
    ]
    world = World(rooms, items)
    state = GameState(current_room="room1")
    state.set_flag("door_open")
    state.set_counter("health", 5)
    return state, world


def test_carrying_true(setup):
    state, world = setup
    c = Condition(type=ConditionType.CARRYING, target="sword")
    assert evaluate(c, state, world) is True


def test_carrying_false(setup):
    state, world = setup
    c = Condition(type=ConditionType.CARRYING, target="key")
    assert evaluate(c, state, world) is False


def test_not_carrying(setup):
    state, world = setup
    c = Condition(type=ConditionType.NOT_CARRYING, target="key")
    assert evaluate(c, state, world) is True


def test_here_true(setup):
    state, world = setup
    c = Condition(type=ConditionType.HERE, target="key")
    assert evaluate(c, state, world) is True


def test_here_false(setup):
    state, world = setup
    c = Condition(type=ConditionType.HERE, target="sword")
    assert evaluate(c, state, world) is False


def test_not_here(setup):
    state, world = setup
    c = Condition(type=ConditionType.NOT_HERE, target="sword")
    assert evaluate(c, state, world) is True


def test_in_room(setup):
    state, world = setup
    c = Condition(type=ConditionType.IN_ROOM, target="room1")
    assert evaluate(c, state, world) is True


def test_not_in_room(setup):
    state, world = setup
    c = Condition(type=ConditionType.NOT_IN_ROOM, target="room2")
    assert evaluate(c, state, world) is True


def test_flag_set(setup):
    state, world = setup
    c = Condition(type=ConditionType.FLAG_SET, target="door_open")
    assert evaluate(c, state, world) is True


def test_flag_unset(setup):
    state, world = setup
    c = Condition(type=ConditionType.FLAG_UNSET, target="never_set")
    assert evaluate(c, state, world) is True


def test_counter_ge(setup):
    state, world = setup
    c = Condition(type=ConditionType.COUNTER_GE, target="health", value=5)
    assert evaluate(c, state, world) is True
    c2 = Condition(type=ConditionType.COUNTER_GE, target="health", value=6)
    assert evaluate(c2, state, world) is False


def test_counter_le(setup):
    state, world = setup
    c = Condition(type=ConditionType.COUNTER_LE, target="health", value=5)
    assert evaluate(c, state, world) is True


def test_counter_eq(setup):
    state, world = setup
    c = Condition(type=ConditionType.COUNTER_EQ, target="health", value=5)
    assert evaluate(c, state, world) is True


def test_exists_true(setup):
    state, world = setup
    c = Condition(type=ConditionType.EXISTS, target="key")
    assert evaluate(c, state, world) is True


def test_exists_false(setup):
    state, world = setup
    c = Condition(type=ConditionType.EXISTS, target="ghost")
    assert evaluate(c, state, world) is False


def test_evaluate_all_true(setup):
    state, world = setup
    conditions = [
        Condition(type=ConditionType.IN_ROOM, target="room1"),
        Condition(type=ConditionType.FLAG_SET, target="door_open"),
    ]
    assert evaluate_all(conditions, state, world) is True


def test_evaluate_all_false(setup):
    state, world = setup
    conditions = [
        Condition(type=ConditionType.IN_ROOM, target="room1"),
        Condition(type=ConditionType.FLAG_SET, target="nonexistent"),
    ]
    assert evaluate_all(conditions, state, world) is False


def test_evaluate_all_empty(setup):
    state, world = setup
    assert evaluate_all([], state, world) is True
