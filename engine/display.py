"""Text formatting and display helpers."""

from __future__ import annotations

import textwrap


WIDTH = 72


def wrap(text: str, width: int = WIDTH) -> str:
    lines = text.split("\n")
    wrapped = []
    for line in lines:
        if line.strip() == "":
            wrapped.append("")
        else:
            wrapped.extend(textwrap.wrap(line, width=width))
    return "\n".join(wrapped)


def print_messages(messages: list[str]) -> None:
    for msg in messages:
        print(wrap(msg))


def print_title(title: str) -> None:
    border = "=" * WIDTH
    print(border)
    centered = title.center(WIDTH)
    print(centered)
    print(border)


def print_separator() -> None:
    print("-" * WIDTH)
