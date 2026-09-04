"""Tests for holdem.domain.hands (hand evaluation).

Ported 1:1 from game/tests/test_detector.py — 36 cases.
"""

from __future__ import annotations

from holdem.domain.cards import Card, HandRank, Rank, Suit
from holdem.domain.hands import (
    create_histogram,
    find_best_hand,
    get_high_card_score,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_cards(cards_str: str, hole: str = "") -> tuple[list[Card], list[Card]]:
    """Parse shorthand notation into (table, hole) card lists.

    Format: ``"As Kh 7d 4c 2s"``
    - First char: rank  (A K Q J T 9-2)
    - Second char: suit (s h d c)
    """
    rank_map = {
        "A": Rank.ACE,
        "K": Rank.KING,
        "Q": Rank.QUEEN,
        "J": Rank.JACK,
        "T": Rank.TEN,
        "9": Rank.NINE,
        "8": Rank.EIGHT,
        "7": Rank.SEVEN,
        "6": Rank.SIX,
        "5": Rank.FIVE,
        "4": Rank.FOUR,
        "3": Rank.THREE,
        "2": Rank.TWO,
    }
    suit_map = {
        "s": Suit.SPADES,
        "h": Suit.HEARTS,
        "d": Suit.DIAMONDS,
        "c": Suit.CLUBS,
    }

    def parse(s: str) -> Card:
        return Card(rank_map[s[0]], suit_map[s[1]])

    table = [parse(c) for c in cards_str.split()]
    hole_cards = [parse(c) for c in hole.split()] if hole else []
    return table, hole_cards


# ---------------------------------------------------------------------------
# Hand rank detection
# ---------------------------------------------------------------------------


def test_high_card() -> None:
    table, hole = make_cards("Ks Qh Js 9h", hole="Ah")
    assert find_best_hand(table, hole).rank == HandRank.HIGH_CARD


def test_pair() -> None:
    table, hole = make_cards("Kh Qh Jh", hole="Ah As")
    assert find_best_hand(table, hole).rank == HandRank.PAIR


def test_two_pairs() -> None:
    table, hole = make_cards("Qh", hole="Ah As Kh Ks")
    assert find_best_hand(table, hole).rank == HandRank.TWO_PAIR


def test_three_of_a_kind() -> None:
    table, hole = make_cards("Kh Qh", hole="Ah As Ah")
    assert find_best_hand(table, hole).rank == HandRank.THREE_OF_A_KIND


def test_straight() -> None:
    table, hole = make_cards("9h 8c 7d", hole="6s 5h")
    assert find_best_hand(table, hole).rank == HandRank.STRAIGHT


def test_flush() -> None:
    table, hole = make_cards("Kh Qh Jh 9h", hole="Ah")
    assert find_best_hand(table, hole).rank == HandRank.FLUSH


def test_full_house() -> None:
    table, hole = make_cards("Kh Ks", hole="Ah As Ah")
    assert find_best_hand(table, hole).rank == HandRank.FULL_HOUSE


def test_four_of_a_kind() -> None:
    table, hole = make_cards("Kh", hole="Ah As Ah Ah")
    assert find_best_hand(table, hole).rank == HandRank.FOUR_OF_A_KIND


def test_straight_flush() -> None:
    table, hole = make_cards("9h 8h 7h", hole="6h 5h")
    assert find_best_hand(table, hole).rank == HandRank.STRAIGHT_FLUSH


def test_royal_flush() -> None:
    table, hole = make_cards("Kh Qh Jh Th", hole="Ah")
    assert find_best_hand(table, hole).rank == HandRank.ROYAL_FLUSH


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


def test_histogram_creation() -> None:
    table, _ = make_cards("Ah As Kh Qh Jh")
    histogram = create_histogram(table)
    assert histogram[Rank.ACE] == 2
    assert histogram[Rank.KING] == 1
    assert histogram[Rank.QUEEN] == 1
    assert histogram[Rank.JACK] == 1


def test_high_card_score() -> None:
    table, _ = make_cards("Kh Ah Qh Jh Th")
    assert get_high_card_score(table) == (14, 13, 12, 11, 10)


# ---------------------------------------------------------------------------
# Edge-case detection
# ---------------------------------------------------------------------------


def test_flush_not_straight() -> None:
    table, hole = make_cards("4h 8s As Qs 6d", hole="Ks 5s")
    assert find_best_hand(table, hole).rank == HandRank.FLUSH


def test_wheel_straight() -> None:
    table, hole = make_cards("2c 3d 4h", hole="Ah 5h")
    assert find_best_hand(table, hole).rank == HandRank.STRAIGHT


def test_ace_low_straight_flush() -> None:
    table, hole = make_cards("2h 3h 4h", hole="Ah 5h")
    assert find_best_hand(table, hole).rank == HandRank.STRAIGHT_FLUSH


def test_multiple_possible_hands() -> None:
    table, hole = make_cards("Ac Kh Ks Qh Qs", hole="Ah As")
    assert find_best_hand(table, hole).rank == HandRank.FULL_HOUSE


# ---------------------------------------------------------------------------
# Hand comparison tests
# ---------------------------------------------------------------------------


def test_high_card_comparison() -> None:
    t1, h1 = make_cards("Ks Qh Js 9h", hole="Ah")
    t2, h2 = make_cards("Kh Qs Jh 8h", hole="As")
    s1 = find_best_hand(t1, h1)
    s2 = find_best_hand(t2, h2)
    assert s1.high_card_score > s2.high_card_score


def test_pair_comparison() -> None:
    t1, h1 = make_cards("Kh Qh Jh", hole="Ah As")
    t2, h2 = make_cards("Kh Qh Th", hole="Ah As")
    s1 = find_best_hand(t1, h1)
    s2 = find_best_hand(t2, h2)
    assert s1.high_card_score > s2.high_card_score


def test_two_pair_comparison() -> None:
    t1, h1 = make_cards("Qh", hole="Ah As Kh Ks")
    t2, h2 = make_cards("Qh", hole="Ah As Kh Ks Jh")
    s1 = find_best_hand(t1, h1)
    s2 = find_best_hand(t2, h2)
    assert s1.high_card_score == s2.high_card_score


def test_three_of_a_kind_comparison() -> None:
    t1, h1 = make_cards("Kh Qh", hole="Ah As Ah")
    t2, h2 = make_cards("Kh Jh", hole="Ah As Ah")
    s1 = find_best_hand(t1, h1)
    s2 = find_best_hand(t2, h2)
    assert s1.high_card_score > s2.high_card_score


def test_straight_comparison() -> None:
    t1, h1 = make_cards("Qh Jh Th 9h", hole="Kh")
    t2, h2 = make_cards("Jh Th 9h 8h", hole="Qh")
    s1 = find_best_hand(t1, h1)
    s2 = find_best_hand(t2, h2)
    assert s1.high_card_score > s2.high_card_score


def test_flush_comparison() -> None:
    t1, h1 = make_cards("Kh Qh Jh Th", hole="Ah")
    t2, h2 = make_cards("Qh Jh Th 9h", hole="Kh")
    s1 = find_best_hand(t1, h1)
    s2 = find_best_hand(t2, h2)
    assert s1.high_card_score > s2.high_card_score


def test_full_house_comparison() -> None:
    t1, h1 = make_cards("Kh Ks", hole="Ah As Ah")
    t2, h2 = make_cards("Ah As", hole="Kh Ks Kh")
    s1 = find_best_hand(t1, h1)
    s2 = find_best_hand(t2, h2)
    assert s1.high_card_score > s2.high_card_score


def test_four_of_a_kind_comparison() -> None:
    t1, h1 = make_cards("Kh", hole="Ah As Ah Ah")
    t2, h2 = make_cards("Qh", hole="Ah As Ah Ah")
    s1 = find_best_hand(t1, h1)
    s2 = find_best_hand(t2, h2)
    assert s1.high_card_score > s2.high_card_score


def test_straight_flush_comparison() -> None:
    t1, h1 = make_cards("Qh Jh Th 9h", hole="Kh")
    t2, h2 = make_cards("Jh Th 9h 8h", hole="Qh")
    s1 = find_best_hand(t1, h1)
    s2 = find_best_hand(t2, h2)
    assert s1.high_card_score > s2.high_card_score


def test_royal_flush_vs_straight_flush() -> None:
    t1, h1 = make_cards("Ks Qs Js Ts", hole="As")
    t2, h2 = make_cards("Qs Js Ts 9s", hole="Ks")
    s1 = find_best_hand(t1, h1)
    s2 = find_best_hand(t2, h2)
    assert s1.rank > s2.rank


# ---------------------------------------------------------------------------
# Structural / card-selection tests
# ---------------------------------------------------------------------------


def test_flush_must_keep_suit() -> None:
    table, hole = make_cards("3h 4h 5h 7h As", hole="2h 9c")
    score = find_best_hand(table, hole)
    assert score.rank == HandRank.FLUSH
    assert all(c.suit == Suit.HEARTS for c in score.cards)


def test_full_house_double_trips() -> None:
    table, hole = make_cards("3c 3d 3s 2c 2d", hole="2s Kh")
    score = find_best_hand(table, hole)
    assert score.rank == HandRank.FULL_HOUSE
    ranks = [c.rank for c in score.cards]
    assert ranks.count(Rank.THREE) == 3
    assert ranks.count(Rank.TWO) == 2


def test_wheel_straight_flush() -> None:
    table, hole = make_cards("Ah Kh 5h 4h 3h", hole="2h Tc")
    assert find_best_hand(table, hole).rank == HandRank.STRAIGHT_FLUSH


def test_high_card_with_score() -> None:
    table, hole = make_cards("As Kh 7d 4c 2s", hole="Jc 9h")
    score = find_best_hand(table, hole)
    assert score.rank == HandRank.HIGH_CARD
    assert score.high_card_score == (14, 13, 11, 9, 7)


def test_two_pair_board_pair_in_hole() -> None:
    table, hole = make_cards("5c 5d Ks 8h 2h", hole="Kh 8c")
    score = find_best_hand(table, hole)
    assert score.rank == HandRank.TWO_PAIR
    assert score.high_card_score == (13, 13, 8, 8, 5)


def test_pair_and_kicker_order() -> None:
    table, hole = make_cards("5c 5d Ks 8h 2h", hole="Kh 9c")
    score = find_best_hand(table, hole)
    assert score.rank == HandRank.TWO_PAIR
    assert score.high_card_score == (13, 13, 9, 8, 5)


def test_three_of_kind_vs_full_house() -> None:
    table, hole = make_cards("7s 7h 7d Kc 2c", hole="Kd 2d")
    score = find_best_hand(table, hole)
    assert score.rank == HandRank.FULL_HOUSE
    assert score.high_card_score == (13, 13, 7, 7, 7)


def test_wheel_straight_with_score() -> None:
    table, hole = make_cards("Ah 2c 3d 4h 5s", hole="9c Jh")
    score = find_best_hand(table, hole)
    assert score.rank == HandRank.STRAIGHT
    assert score.high_card_score == (5, 4, 3, 2, 14)


def test_straight_flush_and_royal_flush_priority() -> None:
    t1, h1 = make_cards("Ks Qs Js Ts 9s", hole="As 2s")
    t2, h2 = make_cards("Ks Qs Js Ts 9s", hole="8s 7s")
    s1 = find_best_hand(t1, h1)
    s2 = find_best_hand(t2, h2)
    assert s1.rank == HandRank.ROYAL_FLUSH
    assert s2.rank == HandRank.STRAIGHT_FLUSH
    assert s1.rank > s2.rank


def test_issue_flush_vs_straight() -> None:
    # community: 4h 8s As Qs 6c  /  hole: Ks 5s  →  flush (spades), not straight
    table, hole = make_cards("4h 8s As Qs 6c", hole="Ks 5s")
    assert find_best_hand(table, hole).rank == HandRank.FLUSH
