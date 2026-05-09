"""Tests for shaykopi.catalog.matcher.parse_title."""

from __future__ import annotations

import pytest

from shaykopi.catalog.matcher import parse_title
from shaykopi.models import Game


@pytest.mark.parametrize(
    "title,expected_game,expected_number,expected_grade,expected_variant",
    [
        (
            "Pokemon Charizard ex 199/165 Special Illustration Rare 151 PSA 10 NM",
            Game.POKEMON, "199", "PSA 10", "sir",
        ),
        (
            "Pokémon TCG Pikachu #25 Reverse Holo NM",
            Game.POKEMON, "25", None, "reverse_holo",
        ),
        (
            "One Piece OP01-005 Monkey D. Luffy Leader Card Romance Dawn",
            Game.ONEPIECE, "005", None, "normal",
        ),
        (
            "ONE PIECE TCG ST-01 Roronoa Zoro 010 BGS 9.5",
            Game.ONEPIECE, "010", "BGS 9.5", "normal",
        ),
        (
            "Charizard 1st Edition Shadowless Holo 4/102 CGC 8",
            Game.POKEMON, "4", "CGC 8", "first_edition",  # 1st edition wins on length tie-break
        ),
    ],
)
def test_parse_title(title, expected_game, expected_number, expected_grade, expected_variant):
    parsed = parse_title(title)
    assert parsed.game == expected_game
    assert parsed.number == expected_number
    assert parsed.grade == expected_grade
    assert parsed.variant == expected_variant


def test_parse_title_grade_takes_precedence_over_condition():
    parsed = parse_title("Charizard 199/165 PSA 10 NM")
    assert parsed.grade == "PSA 10"
    assert parsed.condition is None  # graded slabs aren't given a raw condition


def test_parse_title_returns_blank_for_garbage():
    parsed = parse_title("")
    assert parsed.game is None
    assert parsed.number is None
    assert parsed.grade is None


def test_parse_title_onepiece_normalises_set_code():
    parsed = parse_title("One Piece OP1-5 Luffy")
    assert parsed.set_code == "OP-01"
    assert parsed.number == "005"
