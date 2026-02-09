#!/usr/bin/env python3
"""Generate an SVG map of Void Station Omega. No dependencies beyond stdlib."""

import json
from pathlib import Path

# Layout: Deck A on top, Deck B bottom-left, Deck C bottom-right
# This makes the image roughly square so qlmanage doesn't crop it.

RW, RH = 120, 44  # room box size

# All positions are (center_x, center_y)
POSITIONS = {
    # ── DECK A (top, spanning full width) ──
    "bridge":            (680, 90),
    "cryo_bay":          (300, 90),
    "medbay":            (460, 90),
    "deck_a_corridor_1": (300, 180),
    "command_center":    (680, 180),
    "mess_hall":         (140, 270),
    "deck_a_corridor_2": (300, 270),
    "security":          (460, 270),
    "officers_quarters": (300, 360),

    # ── DECK B (bottom-left) ──
    "lab_c2":            (80,  510),
    "deck_b_corridor_1": (230, 510),
    "lab_c1":            (380, 510),
    "alien_chamber":     (80,  610),
    "lab_c4":            (80,  700),
    "deck_b_corridor_2": (230, 700),
    "lab_c3":            (380, 700),
    "server_room":       (230, 800),
    "observation_deck":  (380, 800),

    # ── DECK C (bottom-right) ──
    "escape_pod_bay":    (660, 510),
    "deck_c_corridor":   (660, 610),
    "life_support":      (520, 610),
    "reactor_room":      (800, 610),
    "cargo_hold":        (520, 720),
    "maintenance_shaft": (800, 720),
    "eva_prep":          (800, 820),
    "airlock":           (800, 910),
}

DECK_COLORS = {
    "a": {"fill": "#111830", "stroke": "#3366aa", "text": "#aaccff", "label": "#5588cc"},
    "b": {"fill": "#0f1f15", "stroke": "#338855", "text": "#aaffcc", "label": "#448866"},
    "c": {"fill": "#1f1510", "stroke": "#aa6633", "text": "#ffccaa", "label": "#886644"},
}

ROOM_DECK = {
    "cryo_bay": "a", "medbay": "a", "deck_a_corridor_1": "a",
    "command_center": "a", "bridge": "a", "deck_a_corridor_2": "a",
    "security": "a", "officers_quarters": "a", "mess_hall": "a",
    "deck_b_corridor_1": "b", "deck_b_corridor_2": "b",
    "lab_c1": "b", "lab_c2": "b", "lab_c3": "b", "lab_c4": "b",
    "server_room": "b", "observation_deck": "b", "alien_chamber": "b",
    "deck_c_corridor": "c", "reactor_room": "c", "life_support": "c",
    "maintenance_shaft": "c", "cargo_hold": "c", "eva_prep": "c",
    "airlock": "c", "escape_pod_bay": "c",
}

SPECIAL = {
    "cryo_bay":          {"stroke": "#44aaff", "pw": 3},
    "escape_pod_bay":    {"stroke": "#ffaa44", "pw": 3},
    "alien_chamber":     {"stroke": "#cc44cc", "pw": 3},
    "maintenance_shaft": {"fill": "#0a0a0a"},
}

DISPLAY_NAMES = {
    "cryo_bay": "Cryo Bay\n(START)",
    "medbay": "Medbay",
    "deck_a_corridor_1": "Corridor (Fore)",
    "command_center": "Command\nCenter",
    "bridge": "Bridge",
    "deck_a_corridor_2": "Corridor (Aft)",
    "security": "Security",
    "officers_quarters": "Officers'\nQuarters",
    "mess_hall": "Mess Hall",
    "deck_b_corridor_1": "Corridor (Fore)",
    "deck_b_corridor_2": "Corridor (Aft)",
    "lab_c1": "Lab C-1\nChemistry",
    "lab_c2": "Lab C-2\nXenobiology",
    "lab_c3": "Lab C-3\nPhysics",
    "lab_c4": "Lab C-4\nEng Research",
    "server_room": "Server Room",
    "observation_deck": "Observation\nDeck",
    "alien_chamber": "Alien\nChamber",
    "deck_c_corridor": "Corridor",
    "reactor_room": "Reactor Room",
    "life_support": "Life Support",
    "maintenance_shaft": "Maint. Shaft\n(DARK)",
    "cargo_hold": "Cargo Hold",
    "eva_prep": "EVA Prep",
    "airlock": "Airlock",
    "escape_pod_bay": "Escape Pods\n(GOAL)",
}

OPPOSITE = {"north": "south", "south": "north", "east": "west",
            "west": "east", "up": "down", "down": "up"}

DIR_LABEL = {"north": "N", "south": "S", "east": "E", "west": "W",
             "up": "U", "down": "D"}


def edge_point(cx, cy, direction):
    if direction in ("north", "up"):
        return cx, cy - RH // 2
    if direction in ("south", "down"):
        return cx, cy + RH // 2
    if direction == "east":
        return cx + RW // 2, cy
    if direction == "west":
        return cx - RW // 2, cy
    return cx, cy


def svg_room(room_id):
    cx, cy = POSITIONS[room_id]
    deck = ROOM_DECK[room_id]
    colors = DECK_COLORS[deck]
    sp = SPECIAL.get(room_id, {})
    fill = sp.get("fill", colors["fill"])
    stroke = sp.get("stroke", colors["stroke"])
    pw = sp.get("pw", 1.5)
    tc = colors["text"]
    x, y = cx - RW // 2, cy - RH // 2
    lines = DISPLAY_NAMES.get(room_id, room_id).split("\n")

    s = [f'<rect x="{x}" y="{y}" width="{RW}" height="{RH}" '
         f'rx="6" fill="{fill}" stroke="{stroke}" stroke-width="{pw}"/>']
    if len(lines) == 1:
        s.append(f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" '
                 f'fill="{tc}" font-size="10" font-family="Helvetica,sans-serif">'
                 f'{lines[0]}</text>')
    else:
        ty = cy - 5 * (len(lines) - 1)
        for ln in lines:
            s.append(f'<text x="{cx}" y="{ty + 4}" text-anchor="middle" '
                     f'fill="{tc}" font-size="9" '
                     f'font-family="Helvetica,sans-serif">{ln}</text>')
            ty += 13
    return "\n    ".join(s)


def svg_edge(r1, direction, r2, locked, drawn):
    key = tuple(sorted([r1, r2]))
    if key in drawn or r1 not in POSITIONS or r2 not in POSITIONS:
        return ""
    drawn.add(key)

    cx1, cy1 = POSITIONS[r1]
    cx2, cy2 = POSITIONS[r2]
    rev = OPPOSITE.get(direction, "")
    x1, y1 = edge_point(cx1, cy1, direction)
    x2, y2 = edge_point(cx2, cy2, rev)

    vert = direction in ("up", "down")
    color = "#4488bb" if vert else "#556677"
    pw = 2 if vert else 1.5
    extra = ""
    if locked:
        color = "#cc4444"
        extra = ' stroke-dasharray="6,4"'

    s = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
         f'stroke="{color}" stroke-width="{pw}"{extra}/>']

    lbl = DIR_LABEL.get(direction, "")
    if lbl:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ox = 8 if not vert else 8
        oy = -6 if vert else -6
        s.append(f'<text x="{mx + ox}" y="{my + oy}" text-anchor="middle" '
                 f'fill="{color}" font-size="7" opacity="0.8" '
                 f'font-family="Helvetica,sans-serif">{lbl}</text>')

    return "\n    ".join(s)


def generate():
    data_dir = Path(__file__).parent / "game_data"
    rooms_data = json.loads((data_dir / "rooms.json").read_text())

    W, H = 920, 970
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="#08080f"/>',
        # Title
        '<text x="460" y="28" text-anchor="middle" fill="#cccccc" '
        'font-size="18" font-family="Helvetica,sans-serif" '
        'font-weight="bold">VOID STATION OMEGA</text>',
    ]

    # Deck labels
    for lx, ly, txt, col in [
        (460, 55, "DECK A — Crew Quarters &amp; Operations",
         DECK_COLORS["a"]["label"]),
        (230, 470, "DECK B — Science &amp; Labs",
         DECK_COLORS["b"]["label"]),
        (660, 470, "DECK C — Engineering &amp; Escape",
         DECK_COLORS["c"]["label"]),
    ]:
        svg.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" fill="{col}" '
                   f'font-size="11" font-family="Helvetica,sans-serif" '
                   f'font-style="italic">{txt}</text>')

    # Deck separators
    svg.append('<line x1="30" y1="430" x2="890" y2="430" '
               'stroke="#222233" stroke-width="1" stroke-dasharray="4,6"/>')
    svg.append('<line x1="460" y1="450" x2="460" y2="940" '
               'stroke="#222233" stroke-width="1" stroke-dasharray="4,6"/>')

    # Inter-deck connector labels (Deck A <-> B, Deck B <-> C)
    # A->B: deck_a_corridor_2 (300,360) down to deck_b_corridor_1 (230,510)
    svg.append('<text x="275" y="435" text-anchor="middle" fill="#4488bb" '
               'font-size="8" font-family="Helvetica,sans-serif" opacity="0.7">'
               'ladder</text>')
    # B->C: deck_b_corridor_2 (230,700) down to deck_c_corridor (660,610)
    svg.append('<text x="445" y="655" text-anchor="middle" fill="#4488bb" '
               'font-size="8" font-family="Helvetica,sans-serif" opacity="0.7">'
               'cargo lift</text>')

    # Edges (draw first, under rooms)
    drawn = set()
    for room in rooms_data:
        for ex in room.get("exits", []):
            e = svg_edge(room["id"], ex["direction"], ex["destination"],
                         ex.get("locked", False), drawn)
            if e:
                svg.append(e)

    # Rooms (draw on top)
    for room in rooms_data:
        svg.append(svg_room(room["id"]))

    # Legend
    ly = H - 22
    items = [
        (30, "LEGEND:", "#888888", None),
    ]
    svg.append(f'<text x="30" y="{ly}" fill="#888888" font-size="9" '
               f'font-family="Helvetica,sans-serif">LEGEND:</text>')
    lx = 90
    # locked
    svg.append(f'<line x1="{lx}" y1="{ly - 3}" x2="{lx + 30}" y2="{ly - 3}" '
               f'stroke="#cc4444" stroke-width="2" stroke-dasharray="6,4"/>')
    svg.append(f'<text x="{lx + 35}" y="{ly}" fill="#cc6666" font-size="9" '
               f'font-family="Helvetica,sans-serif">Locked</text>')
    lx += 85
    # up/down
    svg.append(f'<line x1="{lx}" y1="{ly - 3}" x2="{lx + 30}" y2="{ly - 3}" '
               f'stroke="#4488bb" stroke-width="2"/>')
    svg.append(f'<text x="{lx + 35}" y="{ly}" fill="#4488bb" font-size="9" '
               f'font-family="Helvetica,sans-serif">Up / Down</text>')
    lx += 100
    # start
    svg.append(f'<rect x="{lx}" y="{ly - 10}" width="12" height="12" rx="2" '
               f'fill="none" stroke="#44aaff" stroke-width="2"/>')
    svg.append(f'<text x="{lx + 18}" y="{ly}" fill="#44aaff" font-size="9" '
               f'font-family="Helvetica,sans-serif">Start</text>')
    lx += 60
    # goal
    svg.append(f'<rect x="{lx}" y="{ly - 10}" width="12" height="12" rx="2" '
               f'fill="none" stroke="#ffaa44" stroke-width="2"/>')
    svg.append(f'<text x="{lx + 18}" y="{ly}" fill="#ffaa44" font-size="9" '
               f'font-family="Helvetica,sans-serif">Goal</text>')
    lx += 55
    # hidden
    svg.append(f'<rect x="{lx}" y="{ly - 10}" width="12" height="12" rx="2" '
               f'fill="none" stroke="#cc44cc" stroke-width="2"/>')
    svg.append(f'<text x="{lx + 18}" y="{ly}" fill="#cc44cc" font-size="9" '
               f'font-family="Helvetica,sans-serif">Hidden</text>')

    svg.append("</svg>")

    out = Path(__file__).parent / "map.svg"
    out.write_text("\n".join(svg))
    print(f"Written to {out}")


if __name__ == "__main__":
    generate()
