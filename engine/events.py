"""Event manager: evaluates and fires puzzle/story events."""

from __future__ import annotations

from engine.types import (
    Action, ActionType, Event, ItemLocation, ParsedCommand, Timer,
)
from engine.conditions import evaluate_all
from engine.game_state import GameState
from engine.world import World


class EventManager:
    def __init__(self, events: list[Event], timers: list[Timer]) -> None:
        self.events = sorted(events, key=lambda e: -e.priority)
        self._timers_registry: dict[str, Timer] = {}
        for timer in timers:
            self._timers_registry[timer.name] = timer
        self._event_index: dict[str, Event] = {e.id: e for e in events}

    def get_event(self, event_id: str) -> Event | None:
        return self._event_index.get(event_id)

    def try_command_events(self, cmd: ParsedCommand, state: GameState,
                           world: World) -> tuple[bool, list[str]]:
        """Check events matching this command. Returns (handled, messages)."""
        messages: list[str] = []
        handled = False

        for event in self.events:
            if event.verb is None:
                continue  # skip auto-events
            if event.verb != cmd.verb:
                continue
            if event.noun is not None and event.noun != cmd.noun:
                continue
            if event.room is not None and event.room != state.current_room:
                continue

            # Check once-flag
            if event.once and state.flag_is_set(f"event_{event.id}_done"):
                continue

            if not evaluate_all(event.conditions, state, world):
                continue

            # Fire this event
            msgs = self._execute_actions(event.actions, state, world)
            messages.extend(msgs)

            if event.once:
                state.set_flag(f"event_{event.id}_done")

            if event.override_builtin:
                handled = True

            break  # first matching event wins

        return handled, messages

    def run_auto_events(self, state: GameState,
                        world: World) -> list[str]:
        """Run all auto-events (verb=None) whose conditions are met."""
        messages: list[str] = []

        for event in self.events:
            if event.verb is not None:
                continue
            if event.room is not None and event.room != state.current_room:
                continue
            if event.once and state.flag_is_set(f"event_{event.id}_done"):
                continue
            if not evaluate_all(event.conditions, state, world):
                continue

            msgs = self._execute_actions(event.actions, state, world)
            messages.extend(msgs)

            if event.once:
                state.set_flag(f"event_{event.id}_done")

        return messages

    def tick_timers(self, state: GameState,
                    world: World) -> list[str]:
        """Tick all active timers and fire zero-events."""
        messages: list[str] = []
        timer_results = state.tick_timers()

        for name, value, msg in timer_results:
            if msg:
                messages.append(msg)
            if value <= 0:
                timer = self._timers_registry.get(name)
                if timer and timer.on_zero_event:
                    event = self.get_event(timer.on_zero_event)
                    if event:
                        msgs = self._execute_actions(event.actions, state, world)
                        messages.extend(msgs)
                state.disable_timer(name)

        return messages

    def register_timers(self, state: GameState) -> None:
        """Register all timers with game state."""
        for timer in self._timers_registry.values():
            state.register_timer(timer)

    def _execute_actions(self, actions: list[Action], state: GameState,
                         world: World) -> list[str]:
        messages: list[str] = []

        for action in actions:
            at = action.type

            if at == ActionType.MESSAGE:
                messages.append(str(action.value))

            elif at == ActionType.MOVE_ITEM:
                world.move_item(action.target, str(action.value))

            elif at == ActionType.SET_FLAG:
                state.set_flag(action.target)

            elif at == ActionType.CLEAR_FLAG:
                state.clear_flag(action.target)

            elif at == ActionType.INC_COUNTER:
                state.inc_counter(action.target, int(action.value or 1))

            elif at == ActionType.DEC_COUNTER:
                state.dec_counter(action.target, int(action.value or 1))

            elif at == ActionType.SET_COUNTER:
                state.set_counter(action.target, int(action.value or 0))

            elif at == ActionType.TELEPORT:
                state.enter_room(action.target)

            elif at == ActionType.ADD_SCORE:
                state.add_score(int(action.value or 0))

            elif at == ActionType.DESTROY_ITEM:
                world.destroy_item(action.target)

            elif at == ActionType.SWAP_ITEM:
                # target = old item, value = new item ID
                old_item = world.get_item(action.target)
                if old_item:
                    loc = old_item.location
                    world.destroy_item(action.target)
                    world.move_item(str(action.value), loc)

            elif at == ActionType.UNLOCK_EXIT:
                # target = flag to set (which exits check)
                state.set_flag(action.target)

            elif at == ActionType.GAME_OVER:
                state.game_over = True
                state.won = action.value == "win"

            elif at == ActionType.ENABLE_TIMER:
                state.enable_timer(action.target)

            elif at == ActionType.DISABLE_TIMER:
                state.disable_timer(action.target)

        return messages
