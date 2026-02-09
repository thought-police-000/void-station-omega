"""Built-in action handlers for standard verbs."""

from __future__ import annotations

from engine.types import Direction, ItemLocation, ParsedCommand
from engine.game_state import GameState
from engine.world import World


def handle_go(cmd: ParsedCommand, state: GameState,
              world: World) -> list[str]:
    if not cmd.noun:
        return ["Go where?"]

    try:
        direction = Direction(cmd.noun)
    except ValueError:
        return [f"I don't understand the direction '{cmd.noun}'."]

    room = world.get_room(state.current_room)
    if not room:
        return ["You seem to be nowhere at all."]

    ex = world.find_exit(room, direction)
    if not ex:
        return ["You can't go that way."]

    if ex.locked:
        if ex.lock_flag and state.flag_is_set(ex.lock_flag):
            pass  # unlocked by flag
        else:
            return [ex.lock_message]

    dest = world.get_room(ex.destination)
    if not dest:
        return ["That way leads nowhere."]

    first = state.enter_room(dest.id)
    return _describe_room(dest, state, world, first)


def _describe_room(room, state: GameState, world: World,
                   first_visit: bool = False) -> list[str]:
    msgs: list[str] = []

    # Dark room check
    if room.dark and not _has_light(state, world):
        msgs.append(room.dark_description)
        return msgs

    msgs.append(f"\n--- {room.name} ---")
    msgs.append(room.description)

    if first_visit and room.first_visit_text:
        msgs.append(room.first_visit_text)

    # Items in room
    items = world.items_in_room(room.id)
    for item in items:
        if item.room_description:
            msgs.append(item.room_description)

    # Exits
    exits = []
    for ex in room.exits:
        label = ex.direction.value.capitalize()
        if ex.locked and not (ex.lock_flag and state.flag_is_set(ex.lock_flag)):
            label += " (locked)"
        exits.append(label)
    if exits:
        msgs.append("Exits: " + ", ".join(exits))

    return msgs


def _has_light(state: GameState, world: World) -> bool:
    return state.flag_is_set("has_light")


def handle_look(cmd: ParsedCommand, state: GameState,
                world: World) -> list[str]:
    room = world.get_room(state.current_room)
    if not room:
        return ["You see nothing."]
    return _describe_room(room, state, world)


def handle_examine(cmd: ParsedCommand, state: GameState,
                   world: World) -> list[str]:
    if not cmd.noun:
        return ["Examine what?"]

    items = world.resolve_noun_to_items(cmd.noun)
    for item in items:
        if (item.location == state.current_room or
                item.location == ItemLocation.INVENTORY.value):
            return [item.description]

    return [f"You don't see any '{cmd.noun}' here."]


def handle_take(cmd: ParsedCommand, state: GameState,
                world: World) -> list[str]:
    if not cmd.noun:
        return ["Take what?"]

    items = world.resolve_noun_to_items(cmd.noun)
    for item in items:
        if item.location == state.current_room:
            if not item.takeable:
                return [f"You can't take the {item.name}."]
            inv = world.items_in_inventory()
            if len(inv) >= 10:
                return ["You're carrying too much already."]
            world.move_item(item.id, ItemLocation.INVENTORY.value)
            return [f"Taken: {item.name}"]
        if item.location == ItemLocation.INVENTORY.value:
            return ["You already have that."]

    return [f"You don't see any '{cmd.noun}' here."]


def handle_drop(cmd: ParsedCommand, state: GameState,
                world: World) -> list[str]:
    if not cmd.noun:
        return ["Drop what?"]

    items = world.resolve_noun_to_items(cmd.noun)
    for item in items:
        if item.location == ItemLocation.INVENTORY.value:
            world.move_item(item.id, state.current_room)
            return [f"Dropped: {item.name}"]

    return ["You're not carrying that."]


def handle_inventory(cmd: ParsedCommand, state: GameState,
                     world: World) -> list[str]:
    items = world.items_in_inventory()
    if not items:
        return ["You aren't carrying anything."]
    lines = ["You are carrying:"]
    for item in items:
        lines.append(f"  - {item.name}")
    return lines


def handle_use(cmd: ParsedCommand, state: GameState,
               world: World) -> list[str]:
    if not cmd.noun:
        return ["Use what?"]
    return [f"You're not sure how to use that here."]


def handle_combine(cmd: ParsedCommand, state: GameState,
                   world: World) -> list[str]:
    """COMBINE X WITH Y - splits on 'with'."""
    if not cmd.noun:
        return ["Combine what with what?"]

    parts = cmd.noun.split(" with ")
    if len(parts) != 2:
        return ["Try: COMBINE <item> WITH <item>"]

    noun1, noun2 = parts[0].strip(), parts[1].strip()

    items1 = world.resolve_noun_to_items(noun1)
    items2 = world.resolve_noun_to_items(noun2)

    for item1 in items1:
        if item1.location != ItemLocation.INVENTORY.value:
            continue
        for item2 in items2:
            if item2.location != ItemLocation.INVENTORY.value:
                continue
            # Check if they can combine
            if item1.combine_with == item2.id and item1.combine_result:
                world.destroy_item(item1.id)
                world.destroy_item(item2.id)
                world.move_item(item1.combine_result,
                                ItemLocation.INVENTORY.value)
                result_item = world.get_item(item1.combine_result)
                msg = item1.combine_message or (
                    f"You combine the {item1.name} and {item2.name}.")
                if result_item:
                    msg += f" You now have: {result_item.name}"
                return [msg]
            if item2.combine_with == item1.id and item2.combine_result:
                world.destroy_item(item1.id)
                world.destroy_item(item2.id)
                world.move_item(item2.combine_result,
                                ItemLocation.INVENTORY.value)
                result_item = world.get_item(item2.combine_result)
                msg = item2.combine_message or (
                    f"You combine the {item1.name} and {item2.name}.")
                if result_item:
                    msg += f" You now have: {result_item.name}"
                return [msg]

    return ["Those items can't be combined."]


def handle_score(cmd: ParsedCommand, state: GameState,
                 world: World) -> list[str]:
    return [f"Score: {state.score} / {state.max_score}  "
            f"(Turns: {state.turns})"]


# Registry of built-in handlers
BUILTIN_HANDLERS: dict[str, callable] = {
    "go": handle_go,
    "look": handle_look,
    "examine": handle_examine,
    "take": handle_take,
    "drop": handle_drop,
    "inventory": handle_inventory,
    "use": handle_use,
    "combine": handle_combine,
    "score": handle_score,
}
