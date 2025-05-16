#!/usr/bin/python
# vim: set fileencoding=utf-8 :
"""
File: detector.py
Author: dave
Github: https://github.com/davidus27
Description: Library for easier detection of all existing hand values of players.
"""
from cards import Card, Rank
from collections import Counter
from typing import List, Dict, Optional

def create_histogram(cards: List[Card]) -> Dict[Rank, int]:
    return dict(Counter(card.rank for card in cards))

def high_card_score(cards: List[Card]) -> float:
    sorted_cards = sorted(cards, key=lambda c: c.rank.value, reverse=True)
    score = 0.0
    for i, card in enumerate(sorted_cards):
        score += (0.01 ** (i + 1)) * card.rank.value
    return score


def find_n_of_a_kind(histogram: Dict[Rank, int], count: int) -> Optional[List[Rank]]:
    return [rank for rank, c in histogram.items() if c == count]


def get_cards_by_rank(cards: List[Card], ranks: List[Rank]) -> List[Card]:
    return [card for card in cards if card.rank in ranks]


def flush(cards: List[Card]) -> Optional[List[Card]]:
    suit_counts = Counter(card.suit for card in cards)
    for suit, count in suit_counts.items():
        if count >= 5:
            suited_cards = [card for card in cards if card.suit == suit]
            return sorted(suited_cards, key=lambda c: c.rank.value, reverse=True)[:5]
    return None


def straight(cards: List[Card]) -> Optional[List[Card]]:
    unique_cards = {card.rank: card for card in sorted(cards, key=lambda c: c.rank.value, reverse=True)}
    ranks = sorted({r.value for r in unique_cards}, reverse=True)
    if Rank.ACE in unique_cards:
        ranks.append(1)  # Ace can be low

    for i in range(len(ranks) - 4):
        window = ranks[i:i+5]
        if window[0] - window[4] == 4:
            result = [unique_cards[Rank(rank)] if rank != 1 else unique_cards[Rank.ACE] for rank in window]
            return result
    return None


def straight_flush(cards: List[Card]) -> Optional[List[Card]]:
    flush_cards = flush(cards)
    if flush_cards:
        return straight(flush_cards)
    return None


def royal_flush(cards: List[Card]) -> Optional[List[Card]]:
    rf_ranks = {Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE}
    flush_cards = flush(cards)
    if flush_cards and all(rank in [c.rank for c in flush_cards] for rank in rf_ranks):
        return [c for c in flush_cards if c.rank in rf_ranks]
    return None


def full_house(histogram: Dict[Rank, int], cards: List[Card]) -> Optional[List[Card]]:
    three = find_n_of_a_kind(histogram, 3)
    pair = find_n_of_a_kind(histogram, 2)
    if three:
        three_rank = three[0]
        pair_ranks = [r for r in pair if r != three_rank]
        if pair_ranks:
            return get_cards_by_rank(cards, [three_rank] * 3 + [pair_ranks[0]] * 2)
    return None


def two_pairs(histogram: Dict[Rank, int], cards: List[Card]) -> Optional[List[Card]]:
    pairs = find_n_of_a_kind(histogram, 2)
    if len(pairs) >= 2:
        top_pairs = sorted(pairs, key=lambda r: r.value, reverse=True)[:2]
        return get_cards_by_rank(cards, [top_pairs[0]] * 2 + [top_pairs[1]] * 2)
    return None


def find_best_hand(cards: List[Card]) -> float:
    histogram = create_histogram(cards)
    options = [
        royal_flush(cards),              # 9
        straight_flush(cards),          # 8
        get_cards_by_rank(cards, [r] * 4) if (r := next(iter(find_n_of_a_kind(histogram, 4)), None)) else None,  # 7
        full_house(histogram, cards),   # 6
        flush(cards),                   # 5
        straight(cards),                # 4
        get_cards_by_rank(cards, [r] * 3) if (r := next(iter(find_n_of_a_kind(histogram, 3)), None)) else None,  # 3
        two_pairs(histogram, cards),    # 2
        get_cards_by_rank(cards, [r] * 2) if (r := next(iter(find_n_of_a_kind(histogram, 2)), None)) else None   # 1
    ]

    for index, result in enumerate(options):
        if result:
            if index == 0:
                return 9  # Royal flush — max score
            return (9 - index) + high_card_score(result)

    return high_card_score(cards)  # Just high card if no other hand matched



