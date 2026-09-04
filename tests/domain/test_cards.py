"""Card string codec and HandScore ordering."""

from __future__ import annotations

import pytest

from holdem.domain.cards import (
    Card,
    HandRank,
    HandScore,
    Rank,
    Suit,
    format_card,
    format_cards,
    parse_card,
    parse_cards,
)


def test_parse_and_format_roundtrip() -> None:
    text = "As Kh Td 9c 2h"
    cards = parse_cards(text)
    assert len(cards) == 5
    assert format_cards(cards) == text
    assert all(str(card) == format_card(card) for card in cards)


def test_parse_card_case_insensitive() -> None:
    assert parse_card("as") == Card(Rank.ACE, Suit.SPADES)
    assert parse_card("tD") == Card(Rank.TEN, Suit.DIAMONDS)
    assert Card.from_str("Qc") == Card(Rank.QUEEN, Suit.CLUBS)


def test_parse_cards_empty() -> None:
    assert parse_cards("") == ()
    assert parse_cards("   ") == ()


@pytest.mark.parametrize(
    "raw",
    ["", "A", "Ax", "1h", "A♠", "14s", "Ahx", "  "],
)
def test_parse_card_rejects_invalid(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_card(raw)


def test_standard_deck_has_52_unique() -> None:
    from holdem.engine.deck import standard_deck

    deck = standard_deck()
    assert len(deck) == 52
    assert len(set(deck)) == 52


def _score(rank: HandRank, kickers: tuple[int, ...]) -> HandScore:
    return HandScore(rank, kickers, [])


def test_hand_score_rank_orders() -> None:
    pair = _score(HandRank.PAIR, (14, 13, 12, 11))
    flush = _score(HandRank.FLUSH, (10, 9, 8, 7, 6))
    assert pair < flush
    assert flush > pair
    assert pair <= flush
    assert flush >= pair
    assert pair != flush


def test_hand_score_kicker_orders_same_rank() -> None:
    ace_pair = _score(HandRank.PAIR, (14, 13, 12, 11))
    king_pair = _score(HandRank.PAIR, (13, 14, 12, 11))
    assert king_pair < ace_pair
    assert ace_pair > king_pair


def test_hand_score_equal_when_kickers_match() -> None:
    a = _score(HandRank.STRAIGHT, (9, 8, 7, 6, 5))
    b = _score(HandRank.STRAIGHT, (9, 8, 7, 6, 5))
    assert a == b
    assert a <= b
    assert a >= b
    assert not a < b
    assert not a > b


def test_hand_score_eq_rejects_other_types() -> None:
    score = _score(HandRank.HIGH_CARD, (14,))
    assert score != "high"
    assert score != 0
