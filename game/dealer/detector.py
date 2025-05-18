from cards import Card, Rank, HandRank, Suit, HandScore
from typing import List, Dict, Optional, Tuple
from collections import Counter

def create_histogram(cards: List[Card]) -> Dict[Rank, int]:
    return dict(Counter(card.rank for card in cards))


def get_high_card_score(cards: List[Card]) -> Tuple[int, ...]:
    # Special case: A-2-3-4-5 should be (5,4,3,2,14)
    values = [card.rank.value for card in cards]
    if set(values) == {14, 2, 3, 4, 5}:
        return (5, 4, 3, 2, 14)
    return tuple(sorted(values, reverse=True)[:5])


def find_n_of_a_kind(histogram: Dict[Rank, int], count: int) -> List[Rank]:
    matches = [rank for rank, c in histogram.items() if c == count]
    return sorted(matches, key=lambda r: r.value, reverse=True)


# def hand_contributes_to_pair(pair_ranks: List[Rank], hand: List[Card]) -> bool:
#     hand_ranks = {card.rank for card in hand}
#     return any(r in hand_ranks for r in pair_ranks)


def select_kickers(cards: List[Card], kickers: List[Card]) -> List[Card]:
    # we get highest cards that are not in the kickers sorted by rank value
    return sorted([c for c in cards if c not in kickers], key=lambda c: c.rank.value, reverse=True)


def get_cards_by_rank(cards: List[Card], ranks: List[Rank]) -> List[Card]:
    needed = Counter(ranks)
    selected = []

    for card in cards:
        if needed[card.rank] > 0:
            selected.append(card)
            needed[card.rank] -= 1

    return selected


def hand_contributes_to_ranks(ranks: List[Rank], hand: List[Card]) -> bool:
    return any(card.rank in ranks for card in hand)


def flush(cards: List[Card]) -> Optional[List[Card]]:
    suit_counts = Counter(card.suit for card in cards)
    for suit, count in suit_counts.items():
        if count >= 5:
            suited_cards = [card for card in cards if card.suit == suit]
            return sorted(suited_cards, key=lambda c: c.rank.value, reverse=True)[:5]
    return None


def straight(cards: List[Card]) -> Optional[List[Card]]:
    seen = {}
    for card in sorted(cards, key=lambda c: c.rank.value, reverse=True):
        seen.setdefault(card.rank.value, card)

    values = list(seen.keys())
    if 14 in values:
        values.append(1)

    for i in range(len(values) - 4):
        window = values[i:i + 5]
        if window[0] - window[4] == 4 and len(set(window)) == 5:
            return [seen[v if v != 1 else 14] for v in window]
    return None


def straight_flush(cards: List[Card]) -> Optional[List[Card]]:
    suits: Dict[Suit, List[Card]] = {}
    for c in cards:
        suits.setdefault(c.suit, []).append(c)

    best: Optional[List[Card]] = None
    for suited_cards in suits.values():
        if len(suited_cards) < 5:
            continue
        s = straight(suited_cards)          # uses the full suit
        if s and (best is None or s[0].rank.value > best[0].rank.value):
            best = s
    return best


def full_house(histogram: Dict[Rank, int], cards: List[Card]) -> Optional[List[Card]]:
    trips = find_n_of_a_kind(histogram, 3)
    if not trips:
        return None

    three_rank = trips[0]
    three_cards = get_cards_by_rank(cards, [three_rank] * 3)
    used_ids = {id(c) for c in three_cards}

    # Consider additional trips as possible pair source (downgraded trips)
    remaining_trips = trips[1:]
    pairs = find_n_of_a_kind(histogram, 2)
    pair_candidates = remaining_trips + pairs
    for pair_rank in pair_candidates:
        remaining = [c for c in cards if id(c) not in used_ids]
        pair_cards = get_cards_by_rank(remaining, [pair_rank] * 2)
        if len(pair_cards) == 2:
            return three_cards + pair_cards

    return None


def two_pairs(histogram: Dict[Rank, int], cards: List[Card], hand: List[Card]) -> Optional[List[Card]]:
    pairs = find_n_of_a_kind(histogram, 2)
    if len(pairs) >= 2:
        top_pairs = sorted(pairs, key=lambda r: r.value, reverse=True)[:2]
        # if not hand_contributes_to_pair(top_pairs, hand):
        #     return None
        return get_cards_by_rank(cards, [top_pairs[0]] * 2 + [top_pairs[1]] * 2)
    return None

def find_best_hand(table_cards: List[Card], player_cards: List[Card]) -> HandScore:
    """
    Return the strongest five-card poker hand available from the seven cards
    (community + player).  The evaluation short-circuits from strongest
    (Royal Flush) to weakest (High Card).
    """
    cards      = table_cards + player_cards
    histogram  = create_histogram(cards)

    # ------------------------------------------------------------------ #
    # Helper: wrap a list[Card] into a HandScore in one readable line.
    # ------------------------------------------------------------------ #
    def make(rank: HandRank, chosen: List[Card]) -> HandScore:
        return HandScore(rank, get_high_card_score(chosen), chosen[:5]) # we only return the best 5 cards

    # ───────────────────────────────── 1. STRAIGHT-FLUSH FAMILY ─────────────────────────────
    if (sf := straight_flush(cards)):
        is_royal = {c.rank for c in sf} == {Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE}
        return make(HandRank.ROYAL_FLUSH if is_royal else HandRank.STRAIGHT_FLUSH, sf)

    # ───────────────────────────────── 2. FOUR OF A KIND ────────────────────────────────────
    if (quads := find_n_of_a_kind(histogram, 4)):
        quad_cards = get_cards_by_rank(cards, [quads[0]] * 4)
        kicker     = select_kickers(cards, quad_cards)
        return make(HandRank.FOUR_OF_A_KIND, quad_cards + kicker)

    # ───────────────────────────────── 3. FULL HOUSE ───────────────────────────────────────
    if (full := full_house(histogram, cards)):
        return make(HandRank.FULL_HOUSE, full)

    # ───────────────────────────────── 4. FLUSH / STRAIGHT ─────────────────────────────────
    if (f := flush(cards)):
        return make(HandRank.FLUSH, f)

    if (s := straight(cards)):
        return make(HandRank.STRAIGHT, s)

    # ───────────────────────────────── 5. THREE OF A KIND ──────────────────────────────────
    if (trips := find_n_of_a_kind(histogram, 3)):
        three   = get_cards_by_rank(cards, [trips[0]] * 3)
        kickers = select_kickers(cards, three)
        return make(HandRank.THREE_OF_A_KIND, three + kickers)

    # ───────────────────────────────── 6. TWO PAIR ─────────────────────────────────────────
    if (tp := two_pairs(histogram, cards, player_cards)):
        kicker = select_kickers(cards, tp)
        return make(HandRank.TWO_PAIR, tp + kicker)

    # ───────────────────────────────── 7. ONE PAIR ─────────────────────────────────────────
    if (pairs := find_n_of_a_kind(histogram, 2)):
        pair    = get_cards_by_rank(cards, [pairs[0]] * 2)
        kickers = select_kickers(cards, pair)
        return make(HandRank.PAIR, pair + kickers)

    # ───────────────────────────────── 8. HIGH CARD ───────────────────────────────────────
    return make(HandRank.HIGH_CARD, cards)
