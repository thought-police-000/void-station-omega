"""Text formatting and display helpers."""

from __future__ import annotations

import textwrap


WIDTH = 72


class Pager:
    """Pauses output every page_height lines for CRT terminals."""

    def __init__(self, page_height: int = 23, input_fn=None,
                 enabled: bool = True):
        self.page_height = page_height
        self.line_count = 0
        self._input_fn = input_fn or input
        self.enabled = enabled

    def write(self, text: str = "") -> None:
        if not self.enabled:
            print(text)
            return
        for line in text.split("\n"):
            if self.line_count >= self.page_height:
                self._input_fn("[press enter]")
                self.line_count = 0
            print(line)
            self.line_count += 1

    def reset(self) -> None:
        self.line_count = 0


def wrap(text: str, width: int = WIDTH) -> str:
    lines = text.split("\n")
    wrapped = []
    for line in lines:
        if line.strip() == "":
            wrapped.append("")
        else:
            wrapped.extend(textwrap.wrap(line, width=width))
    return "\n".join(wrapped)


def print_messages(messages: list[str], pager: Pager | None = None) -> None:
    out = pager.write if pager else print
    for msg in messages:
        out(wrap(msg))


def print_title(title: str, pager: Pager | None = None) -> None:
    out = pager.write if pager else print
    border = "=" * WIDTH
    out(border)
    out(title.center(WIDTH))
    out(border)


def print_separator(pager: Pager | None = None) -> None:
    out = pager.write if pager else print
    out("-" * WIDTH)
