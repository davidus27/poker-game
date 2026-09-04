"""Read-only views of table state for actors and UIs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from holdem.domain.actions import ActionKind
from holdem.domain.cards import Card


class Street(Enum):
    WAITING = "waiting"
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    HAND_OVER = "hand_over"
    TOURNAMENT_OVER = "tournament_over"


class SeatStatus(Enum):
    ACTIVE = "active"
    FOLDED = "folded"
    ALL_IN = "all_in"
    BUSTED = "busted"


@dataclass(frozen=True)
class LegalAction:
    """One legal choice. For RAISE, ``min_amount`` / ``max_amount`` are raise-to totals."""

    kind: ActionKind
    min_amount: int | None = None
    max_amount: int | None = None


@dataclass(frozen=True)
class PublicSeat:
    seat_id: int
    stack: int
    status: SeatStatus
    street_bet: int
    committed: int


@dataclass(frozen=True)
class PotView:
    amount: int
    eligible: frozenset[int]


@dataclass(frozen=True)
class SeatView:
    """What one seat is allowed to see: public state plus that seat's hole cards."""

    seat_id: int
    street: Street
    hand_number: int
    button: int
    small_blind: int
    big_blind: int
    board: tuple[Card, ...]
    hole: tuple[Card, ...]
    pot_total: int
    pots: tuple[PotView, ...]
    seats: tuple[PublicSeat, ...]
    to_act: int | None
    legal_actions: tuple[LegalAction, ...]
    current_bet: int
    min_raise_to: int | None
