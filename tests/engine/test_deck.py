"""Deck completeness, dealing, and seeded shuffle."""

from __future__ import annotations

import random

import pytest

from holdem.domain.cards import parse_cards
from holdem.engine.deck import Deck, standard_deck
from holdem.engine.exceptions import EngineStateError
from holdem.engine.table import Table
from tests.engine.helpers import build_deck


def test_standard_deck_is_complete() -> None:
    deck = standard_deck()
    assert len(deck) == 52
    ranks = {card.rank for card in deck}
    suits = {card.suit for card in deck}
    assert len(ranks) == 13
    assert len(suits) == 4


def test_draw_reduces_remaining() -> None:
    deck = Deck(list(standard_deck()))
    drawn = deck.draw(5)
    assert len(drawn) == 5
    assert len(deck) == 47
    assert all(card not in deck.remaining() for card in drawn)


def test_seeded_shuffle_is_deterministic() -> None:
    a = Deck(rng=random.Random(7))
    b = Deck(rng=random.Random(7))
    c = Deck(rng=random.Random(8))
    assert a.remaining() == b.remaining()
    assert a.remaining() != c.remaining()


def test_draw_past_end_raises() -> None:
    deck = Deck(list(parse_cards("As Kh")))
    with pytest.raises(EngineStateError):
        deck.draw(3)
    with pytest.raises(ValueError):
        deck.draw(0)


def test_table_deals_two_hole_cards_and_five_board() -> None:
    table = Table(stacks=[100, 100], rng=random.Random(1))
    table.start_hand()
    for seat_id in (0, 1):
        view = table.seat_view(seat_id)
        assert len(view.hole) == 2
    # play to showdown by checking/calling through
    # HU: seat 0 is SB/button, seat 1 is BB. Preflop seat 0 acts first.
    from holdem.domain.actions import Action

    table.apply(Action.call())
    table.apply(Action.check())
    while table.to_act is not None:
        table.apply(Action.check())
    assert len(table.board) == 5
    assert table.is_hand_over


def test_build_deck_deals_requested_holes() -> None:
    cards = build_deck(
        3,
        button=0,
        holes={0: "As Ah", 1: "Ks Kh", 2: "Qs Qh"},
        board="2c 3c 4c 5c 6c",
    )
    table = Table(stacks=[200, 200, 200], rng=random.Random(0))
    table.start_hand(cards=cards)
    assert table.seat_view(0).hole == parse_cards("As Ah")
    assert table.seat_view(1).hole == parse_cards("Ks Kh")
    assert table.seat_view(2).hole == parse_cards("Qs Qh")
    # foreign hole cards stay hidden
    assert table.seat_view(0).hole != table.seat_view(1).hole
    other = table.seat_view(1)
    assert parse_cards("As Ah") != other.hole
