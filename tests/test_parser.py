"""Tests for command parser."""

import pytest
from engine.parser import Parser
from engine.types import Vocabulary


@pytest.fixture
def parser():
    vocab = Vocabulary(
        verb_synonyms={"get": "take", "grab": "take", "l": "look",
                        "x": "examine", "i": "inventory"},
        noun_synonyms={"torch": "flashlight", "card": "keycard"},
        direction_synonyms={"n": "north", "s": "south", "e": "east",
                             "w": "west", "u": "up", "d": "down"},
    )
    return Parser(vocab)


def test_empty_input(parser):
    assert parser.parse("") is None
    assert parser.parse("   ") is None


def test_direction_shortcut(parser):
    cmd = parser.parse("n")
    assert cmd.verb == "go"
    assert cmd.noun == "north"


def test_direction_full(parser):
    cmd = parser.parse("north")
    assert cmd.verb == "go"
    assert cmd.noun == "north"


def test_go_direction(parser):
    cmd = parser.parse("go south")
    assert cmd.verb == "go"
    assert cmd.noun == "south"


def test_go_direction_synonym(parser):
    cmd = parser.parse("go e")
    assert cmd.verb == "go"
    assert cmd.noun == "east"


def test_verb_synonym(parser):
    cmd = parser.parse("get flashlight")
    assert cmd.verb == "take"
    assert cmd.noun == "flashlight"


def test_noun_synonym(parser):
    cmd = parser.parse("take torch")
    assert cmd.verb == "take"
    assert cmd.noun == "flashlight"


def test_both_synonyms(parser):
    cmd = parser.parse("grab card")
    assert cmd.verb == "take"
    assert cmd.noun == "keycard"


def test_single_verb(parser):
    cmd = parser.parse("l")
    assert cmd.verb == "look"
    assert cmd.noun is None


def test_inventory_shortcut(parser):
    cmd = parser.parse("i")
    assert cmd.verb == "inventory"
    assert cmd.noun is None


def test_unknown_verb(parser):
    cmd = parser.parse("dance")
    assert cmd.verb == "dance"
    assert cmd.noun is None


def test_preserves_original(parser):
    cmd = parser.parse("grab torch")
    assert cmd.original_verb == "grab"
    assert cmd.original_noun == "torch"
    assert cmd.verb == "take"
    assert cmd.noun == "flashlight"


def test_case_insensitive(parser):
    cmd = parser.parse("TAKE TORCH")
    assert cmd.verb == "take"
    assert cmd.noun == "flashlight"


def test_multi_word_noun(parser):
    cmd = parser.parse("examine some thing")
    assert cmd.verb == "examine"
    assert cmd.noun == "some thing"
