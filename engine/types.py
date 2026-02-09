"""Core types for the text adventure engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    UP = "up"
    DOWN = "down"


class ItemLocation(Enum):
    """Special item locations beyond room IDs."""
    INVENTORY = "__inventory__"
    NOWHERE = "__nowhere__"


@dataclass
class Exit:
    direction: Direction
    destination: str  # room ID
    locked: bool = False
    lock_flag: str | None = None  # flag that must be set to unlock
    lock_message: str = "The way is blocked."


@dataclass
class Room:
    id: str
    name: str
    description: str
    exits: list[Exit] = field(default_factory=list)
    dark: bool = False
    dark_description: str = "It's pitch black. You can't see a thing."
    first_visit_text: str | None = None
    visit_flag: str | None = None  # flag set on first visit


@dataclass
class Item:
    id: str
    name: str
    description: str  # shown on EXAMINE
    room_description: str  # shown in room ("A flashlight lies on the floor.")
    location: str  # room ID, INVENTORY, or NOWHERE
    takeable: bool = True
    weight: int = 1
    aliases: list[str] = field(default_factory=list)
    combine_with: str | None = None  # item ID this can combine with
    combine_result: str | None = None  # item ID produced by combination
    combine_message: str | None = None


class ConditionType(Enum):
    CARRYING = "carrying"           # player has item
    HERE = "here"                   # item is in current room
    IN_ROOM = "in_room"             # player is in specified room
    FLAG_SET = "flag_set"           # boolean flag is True
    FLAG_UNSET = "flag_unset"       # boolean flag is False
    COUNTER_GE = "counter_ge"       # counter >= value
    COUNTER_LE = "counter_le"       # counter <= value
    COUNTER_EQ = "counter_eq"       # counter == value
    EXISTS = "exists"               # item location != NOWHERE
    NOT_CARRYING = "not_carrying"
    NOT_HERE = "not_here"
    NOT_IN_ROOM = "not_in_room"


@dataclass
class Condition:
    type: ConditionType
    target: str  # item ID, flag name, room ID, or counter name
    value: int | None = None  # for counter comparisons


class ActionType(Enum):
    MESSAGE = "message"               # print text
    MOVE_ITEM = "move_item"           # move item to location
    SET_FLAG = "set_flag"             # set flag to True
    CLEAR_FLAG = "clear_flag"         # set flag to False
    INC_COUNTER = "inc_counter"       # increment counter
    DEC_COUNTER = "dec_counter"       # decrement counter
    SET_COUNTER = "set_counter"       # set counter to value
    TELEPORT = "teleport"             # move player to room
    ADD_SCORE = "add_score"           # add to score
    DESTROY_ITEM = "destroy_item"     # move item to NOWHERE
    SWAP_ITEM = "swap_item"           # replace one item with another
    UNLOCK_EXIT = "unlock_exit"       # set exit's locked to False (via flag)
    GAME_OVER = "game_over"           # end game (win or lose)
    ENABLE_TIMER = "enable_timer"     # start a named countdown
    DISABLE_TIMER = "disable_timer"


@dataclass
class Action:
    type: ActionType
    target: str = ""       # item ID, flag name, room ID, counter name, etc.
    value: Any = None      # text, number, destination, etc.


@dataclass
class Event:
    id: str
    verb: str | None = None        # None = auto-event (runs every turn)
    noun: str | None = None        # None = verb-only match
    room: str | None = None        # None = any room
    conditions: list[Condition] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
    override_builtin: bool = True  # if True, skip built-in action for this verb
    once: bool = False             # if True, only fires once (uses flag "event_{id}_done")
    priority: int = 0              # higher = checked first


@dataclass
class Timer:
    name: str
    counter: str           # counter name to decrement
    interval: int = 1      # turns between decrements
    on_zero_event: str = ""  # event ID to fire when counter hits 0
    message_template: str = ""  # per-tick message, {value} placeholder
    active: bool = False


@dataclass
class Vocabulary:
    verb_synonyms: dict[str, str] = field(default_factory=dict)   # synonym -> canonical
    noun_synonyms: dict[str, str] = field(default_factory=dict)
    direction_synonyms: dict[str, str] = field(default_factory=dict)


@dataclass
class Manifest:
    title: str = "Untitled Adventure"
    author: str = "Unknown"
    version: str = "1.0"
    max_score: int = 0
    max_inventory: int = 10
    start_room: str = ""
    intro_file: str = "intro.txt"
    help_file: str = "help.txt"


@dataclass
class ParsedCommand:
    raw: str
    verb: str
    noun: str | None = None
    original_verb: str = ""
    original_noun: str | None = None
