"""Save/load game state to JSON."""

from __future__ import annotations

import json
from pathlib import Path

from engine.game_state import GameState
from engine.world import World
from engine.types import ItemLocation

SAVE_FILE = "savegame.json"


def save_game(state: GameState, world: World,
              filepath: str = SAVE_FILE) -> str:
    """Save current game state. Returns status message."""
    item_locations = {item_id: item.location
                      for item_id, item in world.items.items()}
    data = {
        "state": state.to_dict(),
        "item_locations": item_locations,
    }
    try:
        Path(filepath).write_text(json.dumps(data, indent=2))
        return f"Game saved to {filepath}."
    except OSError as e:
        return f"Error saving game: {e}"


def load_game(state: GameState, world: World,
              filepath: str = SAVE_FILE) -> str:
    """Load game state from file. Returns status message."""
    path = Path(filepath)
    if not path.exists():
        return "No save file found."
    try:
        data = json.loads(path.read_text())
        state.load_dict(data["state"])
        for item_id, location in data["item_locations"].items():
            if item_id in world.items:
                world.items[item_id].location = location
        return "Game loaded."
    except (json.JSONDecodeError, KeyError, OSError) as e:
        return f"Error loading save: {e}"
