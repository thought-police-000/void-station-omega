"""World data containers: rooms and items indexed for fast lookup."""

from __future__ import annotations

from engine.types import Direction, Exit, Item, ItemLocation, Room


class World:
    def __init__(self, rooms: list[Room], items: list[Item]) -> None:
        self.rooms: dict[str, Room] = {r.id: r for r in rooms}
        self.items: dict[str, Item] = {i.id: i for i in items}
        # Build noun -> item_id lookup (includes aliases)
        self._noun_index: dict[str, list[str]] = {}
        for item in items:
            for name in [item.id] + item.aliases:
                self._noun_index.setdefault(name, []).append(item.id)

    def get_room(self, room_id: str) -> Room | None:
        return self.rooms.get(room_id)

    def get_item(self, item_id: str) -> Item | None:
        return self.items.get(item_id)

    def find_exit(self, room: Room, direction: Direction) -> Exit | None:
        for ex in room.exits:
            if ex.direction == direction:
                return ex
        return None

    def items_in_room(self, room_id: str) -> list[Item]:
        return [i for i in self.items.values() if i.location == room_id]

    def items_in_inventory(self) -> list[Item]:
        return [i for i in self.items.values()
                if i.location == ItemLocation.INVENTORY.value]

    def resolve_noun_to_items(self, noun: str) -> list[Item]:
        """Resolve a noun to matching items (may return multiple)."""
        item_ids = self._noun_index.get(noun, [])
        return [self.items[iid] for iid in item_ids if iid in self.items]

    def move_item(self, item_id: str, location: str) -> None:
        if item_id in self.items:
            self.items[item_id].location = location

    def destroy_item(self, item_id: str) -> None:
        self.move_item(item_id, ItemLocation.NOWHERE.value)
