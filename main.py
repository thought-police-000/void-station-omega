"""Void Station Omega - main game loop."""

from __future__ import annotations

import sys
from pathlib import Path

from engine.types import ParsedCommand
from engine.parser import Parser
from engine.world import World
from engine.game_state import GameState
from engine.events import EventManager
from engine.actions import BUILTIN_HANDLERS, handle_look
from engine.display import print_messages, print_title, print_separator
from engine.save import save_game, load_game
from engine.loader import (
    load_manifest, load_rooms, load_items, load_events,
    load_vocabulary, load_text_file, validate_world,
)

DATA_DIR = Path(__file__).parent / "game_data"


def run(input_fn=None) -> int:
    """Run the game. Returns final score. input_fn overrides input() for testing."""
    if input_fn is None:
        input_fn = input

    # Load game data
    manifest = load_manifest(DATA_DIR)
    rooms = load_rooms(DATA_DIR)
    items = load_items(DATA_DIR)
    events, timers = load_events(DATA_DIR)
    vocabulary = load_vocabulary(DATA_DIR)

    # Validate
    errors = validate_world(rooms, items, events)
    if errors:
        print("DATA ERRORS:")
        for e in errors:
            print(f"  - {e}")
        return -1

    # Initialize
    world = World(rooms, items)
    state = GameState(
        current_room=manifest.start_room,
        max_score=manifest.max_score,
    )
    state.visited.add(manifest.start_room)
    parser = Parser(vocabulary)
    event_mgr = EventManager(events, timers)
    event_mgr.register_timers(state)

    # Intro
    intro = load_text_file(DATA_DIR, manifest.intro_file)
    help_text = load_text_file(DATA_DIR, manifest.help_file)

    print_title(manifest.title)
    if intro:
        print(intro)
    print_separator()

    # Show starting room
    look_cmd = ParsedCommand(raw="look", verb="look")
    msgs = handle_look(look_cmd, state, world)
    print_messages(msgs)

    # Run starting auto-events
    auto_msgs = event_mgr.run_auto_events(state, world)
    if auto_msgs:
        print_messages(auto_msgs)

    # Main loop
    while not state.game_over:
        print()
        try:
            raw = input_fn("> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not raw.strip():
            continue

        # Meta-commands (not counted as turns)
        lower = raw.strip().lower()
        if lower in ("quit", "exit", "q"):
            print("Thanks for playing! Final score: "
                  f"{state.score}/{state.max_score}")
            break
        if lower == "save":
            print(save_game(state, world))
            continue
        if lower == "load":
            print(load_game(state, world))
            # Redisplay room
            msgs = handle_look(look_cmd, state, world)
            print_messages(msgs)
            continue
        if lower in ("help", "?"):
            if help_text:
                print(help_text)
            else:
                print("Available commands: LOOK, GO <dir>, TAKE, DROP, "
                      "EXAMINE, USE, COMBINE, INVENTORY, SCORE, SAVE, "
                      "LOAD, QUIT")
            continue

        # Parse command
        cmd = parser.parse(raw)
        if cmd is None:
            print("I beg your pardon?")
            continue

        state.turns += 1
        messages: list[str] = []

        # 1. Check command events (puzzle/story triggers)
        handled, event_msgs = event_mgr.try_command_events(cmd, state, world)
        messages.extend(event_msgs)

        # 2. If not handled by event, try built-in action
        if not handled:
            handler = BUILTIN_HANDLERS.get(cmd.verb)
            if handler:
                msgs = handler(cmd, state, world)
                messages.extend(msgs)
            else:
                messages.append(f"I don't know how to '{cmd.verb}'.")

        # 3. Display results
        print_messages(messages)

        # 4. Run auto-events (room-enter triggers, etc.)
        auto_msgs = event_mgr.run_auto_events(state, world)
        if auto_msgs:
            print_messages(auto_msgs)

        # 5. Tick timers
        timer_msgs = event_mgr.tick_timers(state, world)
        if timer_msgs:
            print_messages(timer_msgs)

        # 6. Check game over
        if state.game_over:
            if state.won:
                print_separator()
                print(f"*** CONGRATULATIONS! You escaped! ***")
                print(f"Final score: {state.score}/{state.max_score}")
                print(f"Total turns: {state.turns}")
            else:
                print_separator()
                print("*** GAME OVER ***")
                print(f"Score: {state.score}/{state.max_score}")
            break

    return state.score


if __name__ == "__main__":
    run()
