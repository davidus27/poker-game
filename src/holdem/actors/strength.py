"""Pure poker-strength estimates used by heuristic actors."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass

from holdem.domain.cards import Card, Rank
from holdem.domain.hands import find_best_hand, flush, straight
from holdem.domain.views import SeatStatus, SeatView
from holdem.engine.deck import standard_deck

_CHEN_HIGH_CARD: dict[Rank, float] = {
    Rank.ACE: 10.0,
    Rank.KING: 8.0,
    Rank.QUEEN: 7.0,
    Rank.JACK: 6.0,
    Rank.TEN: 5.0,
    Rank.NINE: 4.5,
    Rank.EIGHT: 4.0,
    Rank.SEVEN: 3.5,
    Rank.SIX: 3.0,
    Rank.FIVE: 2.5,
    Rank.FOUR: 2.0,
    Rank.THREE: 1.5,
    Rank.TWO: 1.0,
}


@dataclass(frozen=True)
class DrawOuts:
    """Distinct unseen cards that complete a flush and/or straight."""

    flush: int
    straight: int
    total: int


def _require_hole(hole: Sequence[Card]) -> tuple[Card, Card]:
    if len(hole) != 2:
        raise ValueError("exactly two hole cards are required")
    first, second = hole
    if first == second:
        raise ValueError("hole cards must be distinct")
    return first, second


def chen_score(hole: Sequence[Card]) -> float:
    """Return the Chen formula score for a two-card starting hand.

    Scores are rounded up to the nearest half point, as prescribed by the
    formula. Weak hands may have a negative raw score.
    """

    first, second = _require_hole(hole)
    high, low = sorted((first, second), key=lambda card: card.rank, reverse=True)
    score = _CHEN_HIGH_CARD[high.rank]

    if high.rank == low.rank:
        score = max(5.0, score * 2)
    else:
        if high.suit == low.suit:
            score += 2

        missing_ranks = high.rank.value - low.rank.value - 1
        if missing_ranks == 1:
            score -= 1
        elif missing_ranks == 2:
            score -= 2
        elif missing_ranks == 3:
            score -= 4
        elif missing_ranks >= 4:
            score -= 5

        if missing_ranks <= 1 and high.rank < Rank.QUEEN:
            score += 1

    return math.ceil(score * 2) / 2


def chen_strength(hole: Sequence[Card]) -> float:
    """Return the Chen score normalized and clamped to ``0..1``."""

    return min(1.0, max(0.0, chen_score(hole) / 20.0))


def _validate_known_cards(hole: Sequence[Card], board: Sequence[Card]) -> tuple[Card, ...]:
    known = (*_require_hole(hole), *board)
    if len(board) > 5:
        raise ValueError("board cannot contain more than five cards")
    if len(set(known)) != len(known):
        raise ValueError("known cards must be distinct")
    return known


def count_draw_outs(hole: Sequence[Card], board: Sequence[Card]) -> DrawOuts:
    """Count unseen one-card flush and straight completions.

    Draws are meaningful only on the flop and turn. Cards completing both
    draws are counted once in ``total``.
    """

    known = _validate_known_cards(hole, board)
    if len(board) not in {3, 4}:
        return DrawOuts(flush=0, straight=0, total=0)

    cards = list(known)
    already_flush = flush(cards) is not None
    already_straight = straight(cards) is not None
    flush_cards: set[Card] = set()
    straight_cards: set[Card] = set()

    for candidate in standard_deck():
        if candidate in known:
            continue
        completed = [*cards, candidate]
        if not already_flush and flush(completed) is not None:
            flush_cards.add(candidate)
        if not already_straight and straight(completed) is not None:
            straight_cards.add(candidate)

    return DrawOuts(
        flush=len(flush_cards),
        straight=len(straight_cards),
        total=len(flush_cards | straight_cards),
    )


def draw_equity(hole: Sequence[Card], board: Sequence[Card]) -> float:
    """Estimate improvement chance with the rule of 4 (flop) or 2 (turn)."""

    outs = count_draw_outs(hole, board).total
    multiplier = 0.04 if len(board) == 3 else 0.02 if len(board) == 4 else 0.0
    return min(1.0, outs * multiplier)


def pot_odds(view: SeatView) -> float:
    """Return the fraction of the resulting pot that this seat must call."""

    seat = next((seat for seat in view.seats if seat.seat_id == view.seat_id), None)
    if seat is None:
        raise ValueError(f"seat {view.seat_id} is absent from its SeatView")
    to_call = max(0, view.current_bet - seat.street_bet)
    return to_call / (view.pot_total + to_call) if to_call else 0.0


def monte_carlo_equity(
    view: SeatView,
    rng: random.Random,
    *,
    samples: int = 80,
) -> float:
    """Estimate showdown equity against random in-hand opponent cards.

    A win contributes 1, a tie contributes 0.5, and a loss contributes 0.
    Only the acting seat's private cards and public board are treated as known.
    """

    if samples <= 0:
        raise ValueError("samples must be positive")
    known = _validate_known_cards(view.hole, view.board)
    opponents = sum(
        seat.seat_id != view.seat_id
        and seat.status in {SeatStatus.ACTIVE, SeatStatus.ALL_IN}
        for seat in view.seats
    )
    if opponents == 0:
        return 1.0

    board_needed = 5 - len(view.board)
    cards_needed = board_needed + opponents * 2
    deck = [card for card in standard_deck() if card not in known]
    if cards_needed > len(deck):
        raise ValueError("not enough unseen cards for simulation")

    equity = 0.0
    for _ in range(samples):
        dealt = rng.sample(deck, cards_needed)
        board = [*view.board, *dealt[:board_needed]]
        hero_score = find_best_hand(board, list(view.hole))
        opponent_scores = [
            find_best_hand(
                board,
                dealt[board_needed + index * 2 : board_needed + (index + 1) * 2],
            )
            for index in range(opponents)
        ]
        best_opponent = max(opponent_scores)
        if hero_score > best_opponent:
            equity += 1.0
        elif hero_score == best_opponent:
            equity += 0.5

    return equity / samples
