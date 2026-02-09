"""Tests for event manager."""

import pytest
from engine.events import EventManager
from engine.types import (
    Action, ActionType, Condition, ConditionType, Event, Item,
    ItemLocation, ParsedCommand, Room, Timer,
)
from engine.game_state import GameState
from engine.world import World


@pytest.fixture
def basic_setup():
    rooms = [
        Room(id="room1", name="Room 1", description="A room."),
        Room(id="room2", name="Room 2", description="Another room."),
    ]
    items = [
        Item(id="key", name="key", description="A key.",
             room_description="A key.", location="room1"),
        Item(id="door_item", name="door", description="A door.",
             room_description="", location="room1", takeable=False),
    ]
    world = World(rooms, items)
    state = GameState(current_room="room1")
    return state, world


def test_command_event_fires(basic_setup):
    state, world = basic_setup
    event = Event(
        id="unlock_door",
        verb="use",
        noun="key",
        room="room1",
        conditions=[
            Condition(type=ConditionType.CARRYING, target="key"),
        ],
        actions=[
            Action(type=ActionType.MESSAGE, value="The door unlocks!"),
            Action(type=ActionType.SET_FLAG, target="door_unlocked"),
        ],
    )
    # Move key to inventory
    world.move_item("key", ItemLocation.INVENTORY.value)

    mgr = EventManager([event], [])
    cmd = ParsedCommand(raw="use key", verb="use", noun="key")
    handled, msgs = mgr.try_command_events(cmd, state, world)

    assert handled is True
    assert "The door unlocks!" in msgs
    assert state.flag_is_set("door_unlocked")


def test_command_event_condition_fails(basic_setup):
    state, world = basic_setup
    event = Event(
        id="unlock_door",
        verb="use",
        noun="key",
        room="room1",
        conditions=[
            Condition(type=ConditionType.CARRYING, target="key"),
        ],
        actions=[
            Action(type=ActionType.MESSAGE, value="The door unlocks!"),
        ],
    )
    # Key is in room, not inventory
    mgr = EventManager([event], [])
    cmd = ParsedCommand(raw="use key", verb="use", noun="key")
    handled, msgs = mgr.try_command_events(cmd, state, world)

    assert handled is False
    assert len(msgs) == 0


def test_once_event(basic_setup):
    state, world = basic_setup
    event = Event(
        id="first_look",
        verb="look",
        room="room1",
        conditions=[],
        actions=[
            Action(type=ActionType.MESSAGE, value="First time!"),
        ],
        once=True,
    )
    mgr = EventManager([event], [])
    cmd = ParsedCommand(raw="look", verb="look")

    handled1, msgs1 = mgr.try_command_events(cmd, state, world)
    assert handled1 is True
    assert "First time!" in msgs1

    handled2, msgs2 = mgr.try_command_events(cmd, state, world)
    assert handled2 is False
    assert len(msgs2) == 0


def test_auto_event(basic_setup):
    state, world = basic_setup
    event = Event(
        id="room1_auto",
        verb=None,
        room="room1",
        conditions=[Condition(type=ConditionType.FLAG_UNSET,
                               target="seen_room1")],
        actions=[
            Action(type=ActionType.MESSAGE, value="Welcome!"),
            Action(type=ActionType.SET_FLAG, target="seen_room1"),
        ],
    )
    mgr = EventManager([event], [])

    msgs1 = mgr.run_auto_events(state, world)
    assert "Welcome!" in msgs1
    assert state.flag_is_set("seen_room1")

    msgs2 = mgr.run_auto_events(state, world)
    assert len(msgs2) == 0


def test_priority_ordering(basic_setup):
    state, world = basic_setup
    world.move_item("key", ItemLocation.INVENTORY.value)

    low = Event(
        id="low",
        verb="use",
        noun="key",
        conditions=[Condition(type=ConditionType.CARRYING, target="key")],
        actions=[Action(type=ActionType.MESSAGE, value="LOW")],
        priority=1,
    )
    high = Event(
        id="high",
        verb="use",
        noun="key",
        conditions=[Condition(type=ConditionType.CARRYING, target="key")],
        actions=[Action(type=ActionType.MESSAGE, value="HIGH")],
        priority=10,
    )
    mgr = EventManager([low, high], [])
    cmd = ParsedCommand(raw="use key", verb="use", noun="key")
    _, msgs = mgr.try_command_events(cmd, state, world)
    assert "HIGH" in msgs
    assert "LOW" not in msgs


def test_score_action(basic_setup):
    state, world = basic_setup
    event = Event(
        id="score_test",
        verb="look",
        conditions=[],
        actions=[Action(type=ActionType.ADD_SCORE, value=25)],
        once=True,
    )
    mgr = EventManager([event], [])
    cmd = ParsedCommand(raw="look", verb="look")
    mgr.try_command_events(cmd, state, world)
    assert state.score == 25


def test_teleport_action(basic_setup):
    state, world = basic_setup
    event = Event(
        id="teleport_test",
        verb="use",
        noun="door_item",
        conditions=[],
        actions=[Action(type=ActionType.TELEPORT, target="room2")],
    )
    mgr = EventManager([event], [])
    cmd = ParsedCommand(raw="use door", verb="use", noun="door_item")
    mgr.try_command_events(cmd, state, world)
    assert state.current_room == "room2"


def test_timer_tick(basic_setup):
    state, world = basic_setup
    boom_event = Event(
        id="boom",
        verb=None,
        conditions=[],
        actions=[
            Action(type=ActionType.MESSAGE, value="BOOM!"),
            Action(type=ActionType.GAME_OVER, value="lose"),
        ],
    )
    timer = Timer(
        name="countdown",
        counter="timer_val",
        on_zero_event="boom",
        message_template="T-{value}",
    )
    mgr = EventManager([boom_event], [timer])
    mgr.register_timers(state)
    state.set_counter("timer_val", 2)
    state.enable_timer("countdown")

    msgs1 = mgr.tick_timers(state, world)
    assert any("T-1" in m for m in msgs1)
    assert not state.game_over

    msgs2 = mgr.tick_timers(state, world)
    assert any("BOOM!" in m for m in msgs2)
    assert state.game_over


def test_destroy_item(basic_setup):
    state, world = basic_setup
    event = Event(
        id="destroy_test",
        verb="use",
        noun="key",
        conditions=[],
        actions=[Action(type=ActionType.DESTROY_ITEM, target="key")],
    )
    mgr = EventManager([event], [])
    cmd = ParsedCommand(raw="use key", verb="use", noun="key")
    mgr.try_command_events(cmd, state, world)
    assert world.get_item("key").location == ItemLocation.NOWHERE.value


def test_swap_item(basic_setup):
    state, world = basic_setup
    # Add a new item to swap to
    from engine.types import Item as ItemType
    new_item = ItemType(id="gold_key", name="gold key",
                         description="Shiny.", room_description="",
                         location=ItemLocation.NOWHERE.value)
    world.items["gold_key"] = new_item

    event = Event(
        id="swap_test",
        verb="use",
        noun="key",
        conditions=[],
        actions=[Action(type=ActionType.SWAP_ITEM, target="key",
                         value="gold_key")],
    )
    mgr = EventManager([event], [])
    cmd = ParsedCommand(raw="use key", verb="use", noun="key")
    mgr.try_command_events(cmd, state, world)
    assert world.get_item("key").location == ItemLocation.NOWHERE.value
    assert world.get_item("gold_key").location == "room1"
