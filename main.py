"""Void Station Omega - main game loop."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from engine.types import ParsedCommand
from engine.parser import Parser
from engine.world import World
from engine.game_state import GameState
from engine.events import EventManager
from engine.actions import BUILTIN_HANDLERS, handle_look
from engine.display import Pager, print_messages, print_title, print_separator
from engine.save import save_game, load_game
from engine.loader import (
    load_manifest, load_rooms, load_items, load_events,
    load_vocabulary, load_text_file, validate_world,
)

DEFAULT_DATA_DIR = Path(__file__).parent / "game_data"


def run(input_fn=None, data_dir: Path | None = None) -> int:
    """Run the game. Returns final score. input_fn overrides input() for testing."""
    interactive = input_fn is None
    if input_fn is None:
        input_fn = input
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR
    pager = Pager(input_fn=input_fn, enabled=interactive)

    # Load game data
    manifest = load_manifest(data_dir)
    rooms = load_rooms(data_dir)
    items = load_items(data_dir)
    events, timers = load_events(data_dir)
    vocabulary = load_vocabulary(data_dir)

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
    intro = load_text_file(data_dir, manifest.intro_file)
    help_text = load_text_file(data_dir, manifest.help_file)

    print_title(manifest.title, pager)
    if intro:
        pager.write(intro)
    print_separator(pager)

    # Show starting room
    look_cmd = ParsedCommand(raw="look", verb="look")
    msgs = handle_look(look_cmd, state, world)
    print_messages(msgs, pager)

    # Run starting auto-events
    auto_msgs = event_mgr.run_auto_events(state, world)
    if auto_msgs:
        print_messages(auto_msgs, pager)

    # Main loop
    while not state.game_over:
        pager.write()
        pager.reset()
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
            pager.write("Thanks for playing! Final score: "
                        f"{state.score}/{state.max_score}")
            break
        if lower == "save":
            pager.write(save_game(state, world))
            continue
        if lower == "load":
            pager.write(load_game(state, world))
            # Redisplay room
            msgs = handle_look(look_cmd, state, world)
            print_messages(msgs, pager)
            continue
        if lower in ("help", "?"):
            if help_text:
                pager.write(help_text)
            else:
                pager.write("Available commands: LOOK, GO <dir>, TAKE, DROP, "
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
        print_messages(messages, pager)

        # 4. Run auto-events (room-enter triggers, etc.)
        auto_msgs = event_mgr.run_auto_events(state, world)
        if auto_msgs:
            print_messages(auto_msgs, pager)

        # 5. Tick timers
        timer_msgs = event_mgr.tick_timers(state, world)
        if timer_msgs:
            print_messages(timer_msgs, pager)

        # 6. Check game over
        if state.game_over:
            if state.won:
                print_separator(pager)
                pager.write(f"*** CONGRATULATIONS! You escaped! ***")
                pager.write(f"Final score: {state.score}/{state.max_score}")
                pager.write(f"Total turns: {state.turns}")
            else:
                print_separator(pager)
                pager.write("*** GAME OVER ***")
                pager.write(f"Score: {state.score}/{state.max_score}")
            break

    return state.score


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Text adventure engine")
    parser.add_argument("data_dir", nargs="?", default=None,
                        help="path to game data directory (default: game_data/)")
    args = parser.parse_args()
    data_dir = Path(args.data_dir) if args.data_dir else None
    run(data_dir=data_dir)
