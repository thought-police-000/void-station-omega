"""Condition evaluator for event preconditions."""

from __future__ import annotations

from engine.types import Condition, ConditionType, ItemLocation
from engine.game_state import GameState
from engine.world import World


def evaluate(condition: Condition, state: GameState, world: World) -> bool:
    ct = condition.type
    target = condition.target

    if ct == ConditionType.CARRYING:
        item = world.get_item(target)
        return item is not None and item.location == ItemLocation.INVENTORY.value

    if ct == ConditionType.NOT_CARRYING:
        item = world.get_item(target)
        return item is None or item.location != ItemLocation.INVENTORY.value

    if ct == ConditionType.HERE:
        item = world.get_item(target)
        return item is not None and item.location == state.current_room

    if ct == ConditionType.NOT_HERE:
        item = world.get_item(target)
        return item is None or item.location != state.current_room

    if ct == ConditionType.IN_ROOM:
        return state.current_room == target

    if ct == ConditionType.NOT_IN_ROOM:
        return state.current_room != target

    if ct == ConditionType.FLAG_SET:
        return state.flag_is_set(target)

    if ct == ConditionType.FLAG_UNSET:
        return not state.flag_is_set(target)

    if ct == ConditionType.COUNTER_GE:
        return state.get_counter(target) >= (condition.value or 0)

    if ct == ConditionType.COUNTER_LE:
        return state.get_counter(target) <= (condition.value or 0)

    if ct == ConditionType.COUNTER_EQ:
        return state.get_counter(target) == (condition.value or 0)

    if ct == ConditionType.EXISTS:
        item = world.get_item(target)
        return item is not None and item.location != ItemLocation.NOWHERE.value

    return False


def evaluate_all(conditions: list[Condition], state: GameState,
                 world: World) -> bool:
    return all(evaluate(c, state, world) for c in conditions)
