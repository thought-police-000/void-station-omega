# Void Station Omega

A classic text adventure game in the tradition of Scott Adams and Zork, set on an abandoned deep-space research station.

You awaken in a cryo-pod. The crew is gone. The halls are silent. Something broke containment in the xenobiology labs, and you were left behind. Find a way off the station before it's too late.

## Quick Start

```
python3 main.py
```

No dependencies required — runs on Python 3.10+ with only the standard library.

## Gameplay

```
> look
--- Cryo Bay ---
Rows of cryo-pods line the walls, frost still clinging to the glass.
Only yours is open. Emergency lighting bathes everything in dim red.

> examine pod
The cryo-pod you woke up in. The display reads: 'EMERGENCY REVIVAL —
CREW STATUS: EVACUATED'. You're the only one left.

> south
The hatch is jammed shut. You'll need something to force it open.
```

### Commands

| Command | Short | Description |
|---------|-------|-------------|
| `GO <direction>` | `N S E W U D` | Move between rooms |
| `LOOK` | `L` | Describe the current room |
| `EXAMINE <item>` | `X <item>` | Inspect an item closely |
| `TAKE <item>` | `GET <item>` | Pick up an item |
| `DROP <item>` | | Put down an item |
| `USE <item>` | | Use an item in context |
| `COMBINE <x> WITH <y>` | | Combine two inventory items |
| `INVENTORY` | `I` | List carried items |
| `SCORE` | | Show current score |
| `SAVE` / `LOAD` | | Save or restore progress |
| `QUIT` | `Q` | Exit the game |

## The Station

25 rooms across three decks. 250 maximum score.

## Architecture

The engine is fully data-driven. All game content lives in JSON files under `game_data/`. The engine reads rooms, items, events, and vocabulary from these files at startup. Swap the data directory for an entirely different adventure.

```
engine/          Python engine (parser, state, events, actions)
game_data/       JSON game content + text files
tests/           Unit and integration tests
main.py          Entry point
```

**Command flow:** Input -> Parser (synonym resolution) -> Event Manager (puzzle triggers) -> Built-in Actions (fallback) -> Display

Events take priority over built-in actions, allowing game data to override any verb+noun combination in any room.

## Tests

```
python3 -m pytest tests/ -v
```

57 tests covering the parser, condition evaluator, event system, save/load, data validation (reachability, exit integrity, score totals), and a full automated walkthrough that finishes with 250/250.
