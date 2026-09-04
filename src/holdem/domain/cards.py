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


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.value}"


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
