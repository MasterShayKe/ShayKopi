"""Parse a marketplace listing title into a canonical card identity.

Listings on eBay/Shopify look like:
    "Pokemon Charizard ex 199/165 Special Illustration Rare 151 PSA 10 NM"
    "Charizard ex SIR #199 SV3.5 151 Pokemon TCG"
    "One Piece OP01-005 Monkey D. Luffy Leader Card Romance Dawn"

We extract `(game, set_code, number, variant, condition, grade)`. Whatever we
can't determine is left as None; the matcher is intentionally lossy and the
DB stores the raw title for manual rescue from the dashboard.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..models import Game

# --- Regexes (compiled once) ---------------------------------------------------

# PSA 10, BGS 9.5, CGC 10, SGC 9
_GRADE_RE = re.compile(
    r"\b(PSA|BGS|CGC|SGC|TAG)\s*(10(?:\.0)?|[1-9](?:\.[05])?)\b",
    re.IGNORECASE,
)

# NM, LP, MP, HP, DMG, M, NM/M, Near Mint
_CONDITION_MAP = {
    "M": "mint",
    "MINT": "mint",
    "NM": "near_mint",
    "NM/M": "near_mint",
    "NEAR MINT": "near_mint",
    "LP": "lightly_played",
    "LIGHTLY PLAYED": "lightly_played",
    "MP": "moderately_played",
    "MODERATELY PLAYED": "moderately_played",
    "HP": "heavily_played",
    "HEAVILY PLAYED": "heavily_played",
    "DMG": "damaged",
    "DAMAGED": "damaged",
}
_CONDITION_RE = re.compile(
    r"\b(NM/M|NEAR MINT|LIGHTLY PLAYED|MODERATELY PLAYED|HEAVILY PLAYED|DAMAGED|NM|LP|MP|HP|DMG|MINT|M)\b",
    re.IGNORECASE,
)

# Variant tokens commonly tacked onto Pokemon listings
_VARIANT_TOKENS = {
    "reverse holo": "reverse_holo",
    "reverse foil": "reverse_holo",
    "rev holo": "reverse_holo",
    "holo": "holo",
    "1st edition": "first_edition",
    "first edition": "first_edition",
    "shadowless": "shadowless",
    "full art": "full_art",
    "alt art": "alt_art",
    "alternate art": "alt_art",
    "secret rare": "secret_rare",
    "special illustration rare": "sir",
    "illustration rare": "ir",
    "sir": "sir",
}

# Pokemon: number like "199/165" or "#199" or "199a/165"
_POKEMON_NUMBER_RE = re.compile(r"\b(\d{1,3}[a-zA-Z]?)\s*/\s*(\d{1,3})\b")
_POKEMON_HASH_RE = re.compile(r"#\s*(\d{1,3}[a-zA-Z]?)\b")

# One Piece: set codes look like OP01, OP-01, ST-01, EB-01; numbers like OP01-005
_ONEPIECE_FULL_RE = re.compile(
    r"\b(OP|ST|EB|P)\s*-?\s*(\d{1,3})\s*-\s*(\d{1,3})\b", re.IGNORECASE
)
# Fallbacks when the set code and card number are split by the card name:
# e.g. "ST-01 Roronoa Zoro 010"
_ONEPIECE_SET_ONLY_RE = re.compile(r"\b(OP|ST|EB|P)\s*-?\s*(\d{1,2})\b", re.IGNORECASE)
# Standalone 2-3 digit number (avoid grabbing years / grades)
_ONEPIECE_NUMBER_ONLY_RE = re.compile(r"(?<![/\d])\b(\d{2,3})\b(?!\s*/)")

# Quick game keywords
_POKEMON_HINTS = re.compile(r"\b(pokemon|pokémon|pikachu|charizard|umbreon|eevee|tcg)\b", re.I)
_ONEPIECE_HINTS = re.compile(
    r"\b(one\s*piece|luffy|zoro|nami|usopp|romance\s*dawn|paramount|kingdoms\s*of\s*intrigue)\b",
    re.I,
)


# --- Result type ---------------------------------------------------------------

@dataclass(frozen=True)
class ParsedTitle:
    game: Game | None
    set_code: str | None
    number: str | None
    variant: str
    condition: str | None
    grade: str | None  # e.g. "PSA 10", or None for raw

    @property
    def is_graded(self) -> bool:
        return self.grade is not None


# --- Public API ----------------------------------------------------------------

def parse_title(title: str, *, hint_game: Game | None = None) -> ParsedTitle:
    """Best-effort parse. Never raises; missing pieces become None."""
    if not title:
        return ParsedTitle(None, None, None, "normal", None, None)

    grade = _extract_grade(title)
    condition = None if grade else _extract_condition(title)
    variant = _extract_variant(title)
    game = hint_game or _guess_game(title)

    set_code: str | None = None
    number: str | None = None

    if game == Game.ONEPIECE:
        set_code, number = _extract_onepiece(title)
    elif game == Game.POKEMON:
        # Pokemon set is hard to derive from the title alone; matcher in
        # catalog/pokemon.py reconciles using set_code from product metadata
        # when available. Here we just pull the printed number.
        number = _extract_pokemon_number(title)
    else:
        # No game hint — try One Piece first since OP## codes are
        # unambiguous, then fall back to a Pokemon-ish number.
        set_code, number = _extract_onepiece(title)
        if not number:
            number = _extract_pokemon_number(title)
            if number:
                game = Game.POKEMON
        else:
            game = Game.ONEPIECE

    return ParsedTitle(
        game=game,
        set_code=set_code,
        number=number,
        variant=variant,
        condition=condition,
        grade=grade,
    )


# --- Helpers -------------------------------------------------------------------

def _guess_game(title: str) -> Game | None:
    if _ONEPIECE_HINTS.search(title):
        return Game.ONEPIECE
    if _POKEMON_HINTS.search(title):
        return Game.POKEMON
    return None


def _extract_grade(title: str) -> str | None:
    m = _GRADE_RE.search(title)
    if not m:
        return None
    return f"{m.group(1).upper()} {m.group(2)}"


def _extract_condition(title: str) -> str | None:
    m = _CONDITION_RE.search(title)
    if not m:
        return None
    return _CONDITION_MAP.get(m.group(1).upper())


def _extract_variant(title: str) -> str:
    lower = title.lower()
    # Order matters — match the most specific first.
    for token, variant in sorted(_VARIANT_TOKENS.items(), key=lambda kv: -len(kv[0])):
        if token in lower:
            return variant
    return "normal"


def _extract_pokemon_number(title: str) -> str | None:
    m = _POKEMON_NUMBER_RE.search(title)
    if m:
        return m.group(1)
    m = _POKEMON_HASH_RE.search(title)
    if m:
        return m.group(1)
    return None


def _extract_onepiece(title: str) -> tuple[str | None, str | None]:
    m = _ONEPIECE_FULL_RE.search(title)
    if m:
        prefix, set_num, card_num = m.groups()
        return f"{prefix.upper()}-{int(set_num):02d}", f"{int(card_num):03d}"
    # Fallback: set code somewhere, plus a standalone number elsewhere.
    set_match = _ONEPIECE_SET_ONLY_RE.search(title)
    if not set_match:
        return None, None
    set_code = f"{set_match.group(1).upper()}-{int(set_match.group(2)):02d}"
    # Strip the matched set token from the search space so we don't grab its digits as the number.
    cleaned = title[: set_match.start()] + title[set_match.end():]
    num_match = _ONEPIECE_NUMBER_ONLY_RE.search(cleaned)
    if not num_match:
        return set_code, None
    return set_code, f"{int(num_match.group(1)):03d}"
