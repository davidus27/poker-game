"""Events emitted by the Table state machine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from holdem.domain.actions import Action
from holdem.domain.cards import Card, HandScore
from holdem.domain.views import Street


class BlindKind(Enum):
    SMALL = "small"
    BIG = "big"


@dataclass(frozen=True)
class HandStarted:
    hand_number: int
    button: int
    stacks: tuple[int, ...]


@dataclass(frozen=True)
class BlindPosted:
    seat_id: int
    amount: int
    kind: BlindKind
    is_all_in: bool


@dataclass(frozen=True)
class HoleDealt:
    seat_id: int
    cards: tuple[Card, Card]


@dataclass(frozen=True)
class ActionRequested:
    seat_id: int


@dataclass(frozen=True)
class PlayerActed:
    seat_id: int
    action: Action
    chips: int
    stack: int
    street_bet: int


@dataclass(frozen=True)
class StreetDealt:
    street: Street
    cards: tuple[Card, ...]
    board: tuple[Card, ...]


@dataclass(frozen=True)
class ShowdownHand:
    seat_id: int
    hole: tuple[Card, Card]
    score: HandScore


@dataclass(frozen=True)
class Showdown:
    revelations: tuple[ShowdownHand, ...]


@dataclass(frozen=True)
class PotAward:
    pot_index: int
    amount: int
    winners: tuple[int, ...]
    shares: tuple[int, ...]


@dataclass(frozen=True)
class PotsAwarded:
    awards: tuple[PotAward, ...]


@dataclass(frozen=True)
class PlayerBusted:
    seat_id: int


@dataclass(frozen=True)
class TournamentEnded:
    winner: int


@dataclass(frozen=True)
class HandEnded:
    hand_number: int


Event = (
    HandStarted
    | BlindPosted
    | HoleDealt
    | ActionRequested
    | PlayerActed
    | StreetDealt
    | Showdown
    | PotsAwarded
    | PlayerBusted
    | TournamentEnded
    | HandEnded
)
