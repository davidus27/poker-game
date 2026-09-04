"""Card types: Suit, Rank, Card, HandRank, HandScore.

These are pure value objects – no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum


class Suit(Enum):
    HEARTS = "h"
    DIAMONDS = "d"
    CLUBS = "c"
    SPADES = "s"


class Rank(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


_RANK_FROM_CHAR = {
    "2": Rank.TWO,
    "3": Rank.THREE,
    "4": Rank.FOUR,
    "5": Rank.FIVE,
    "6": Rank.SIX,
    "7": Rank.SEVEN,
    "8": Rank.EIGHT,
    "9": Rank.NINE,
    "T": Rank.TEN,
    "J": Rank.JACK,
    "Q": Rank.QUEEN,
    "K": Rank.KING,
    "A": Rank.ACE,
}
_CHAR_FROM_RANK = {rank: char for char, rank in _RANK_FROM_CHAR.items()}
_SUIT_FROM_CHAR = {suit.value: suit for suit in Suit}


def parse_card(text: str) -> Card:
    """Parse a two-character card string such as ``As`` or ``Td``.

    Rank is ``A K Q J T 9-2`` (case-insensitive). Suit is ``s h d c``.
    """
    raw = text.strip()
    if len(raw) != 2:
        raise ValueError(f"invalid card: {text!r}")
    rank_ch, suit_ch = raw[0].upper(), raw[1].lower()
    rank = _RANK_FROM_CHAR.get(rank_ch)
    suit = _SUIT_FROM_CHAR.get(suit_ch)
    if rank is None or suit is None:
        raise ValueError(f"invalid card: {text!r}")
    return Card(rank, suit)


def format_card(card: Card) -> str:
    """Encode a card as a two-character string such as ``As``."""
    return f"{_CHAR_FROM_RANK[card.rank]}{card.suit.value}"


def parse_cards(text: str) -> tuple[Card, ...]:
    """Parse a space-separated sequence of card strings."""
    parts = text.split()
    if not parts:
        return ()
    return tuple(parse_card(part) for part in parts)


def format_cards(cards: list[Card] | tuple[Card, ...]) -> str:
    """Encode cards as a space-separated string."""
    return " ".join(format_card(card) for card in cards)


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return format_card(self)

    @staticmethod
    def from_str(text: str) -> Card:
        return parse_card(text)


class HandRank(IntEnum):
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9


@dataclass
class HandScore:
    rank: HandRank
    high_card_score: tuple[int, ...]
    cards: list[Card]

    def __lt__(self, other: HandScore) -> bool:
        if self.rank != other.rank:
            return self.rank < other.rank
        return self.high_card_score < other.high_card_score

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HandScore):
            return NotImplemented
        return self.rank == other.rank and self.high_card_score == other.high_card_score

    def __le__(self, other: HandScore) -> bool:
        return self == other or self < other

    def __gt__(self, other: HandScore) -> bool:
        return not self <= other

    def __ge__(self, other: HandScore) -> bool:
        return not self < other
