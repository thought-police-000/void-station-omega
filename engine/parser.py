"""Command parser with synonym resolution."""

from __future__ import annotations

from engine.types import Direction, ParsedCommand, Vocabulary

# Directions that can be typed as bare commands
_DIRECTION_WORDS = {d.value for d in Direction}


class Parser:
    def __init__(self, vocabulary: Vocabulary) -> None:
        self.vocabulary = vocabulary

    def _resolve_direction(self, word: str) -> str | None:
        word = word.lower()
        if word in _DIRECTION_WORDS:
            return word
        return self.vocabulary.direction_synonyms.get(word)

    def _resolve_verb(self, word: str) -> str:
        word = word.lower()
        return self.vocabulary.verb_synonyms.get(word, word)

    def _resolve_noun(self, word: str) -> str:
        word = word.lower()
        resolved = self.vocabulary.noun_synonyms.get(word)
        if resolved:
            return resolved
        # Handle "X with Y" patterns (e.g., "combine cell with adapter")
        if " with " in word:
            left, right = word.split(" with ", 1)
            left = self.vocabulary.noun_synonyms.get(left.strip(), left.strip())
            right = self.vocabulary.noun_synonyms.get(right.strip(), right.strip())
            return f"{left} with {right}"
        return word

    def parse(self, raw_input: str) -> ParsedCommand | None:
        raw = raw_input.strip()
        if not raw:
            return None

        parts = raw.lower().split()

        # Single word: might be a direction shortcut
        if len(parts) == 1:
            direction = self._resolve_direction(parts[0])
            if direction is not None:
                return ParsedCommand(
                    raw=raw,
                    verb="go",
                    noun=direction,
                    original_verb=parts[0],
                    original_noun=parts[0],
                )
            # Single-word verb (LOOK, INVENTORY, HELP, etc.)
            verb = self._resolve_verb(parts[0])
            return ParsedCommand(
                raw=raw,
                verb=verb,
                noun=None,
                original_verb=parts[0],
                original_noun=None,
            )

        # Two-word: verb + noun (or GO + direction)
        original_verb = parts[0]
        original_noun = " ".join(parts[1:])
        verb = self._resolve_verb(original_verb)

        if verb == "go":
            direction = self._resolve_direction(parts[1])
            if direction is not None:
                return ParsedCommand(
                    raw=raw,
                    verb="go",
                    noun=direction,
                    original_verb=original_verb,
                    original_noun=original_noun,
                )

        noun = self._resolve_noun(original_noun)

        return ParsedCommand(
            raw=raw,
            verb=verb,
            noun=noun,
            original_verb=original_verb,
            original_noun=original_noun,
        )
