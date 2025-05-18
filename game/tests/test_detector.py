import unittest
from dealer.detector import (
    find_best_hand, get_high_card_score, create_histogram, HandRank
)
from cards import Card, Suit, Rank



def make_cards(cards_str: str, hole: str = None) -> tuple[list[Card], list[Card]]:
    """
    Helper function to create cards from string notation.
    Format: "As Kh 7d 4c 2s" where:
    - First char is rank (A, K, Q, J, T, 9-2)
    - Second char is suit (s, h, d, c)
    """
    def parse_card(card_str: str) -> Card:
        rank_map = {
            'A': Rank.ACE, 'K': Rank.KING, 'Q': Rank.QUEEN, 'J': Rank.JACK, 'T': Rank.TEN,
            '9': Rank.NINE, '8': Rank.EIGHT, '7': Rank.SEVEN, '6': Rank.SIX,
            '5': Rank.FIVE, '4': Rank.FOUR, '3': Rank.THREE, '2': Rank.TWO
        }
        suit_map = {'s': Suit.SPADES, 'h': Suit.HEARTS, 'd': Suit.DIAMONDS, 'c': Suit.CLUBS}
        return Card(rank_map[card_str[0]], suit_map[card_str[1]])

    table = [parse_card(c) for c in cards_str.split()]
    hole_cards = [parse_card(c) for c in hole.split()] if hole else []
    return table, hole_cards

class TestPokerHandDetector(unittest.TestCase):
    def test_high_card(self):
        table, hole = make_cards("Ks Qh Js 9h", hole="Ah")
        hand_score = find_best_hand(table, hole)
        self.assertEqual(hand_score.rank, HandRank.HIGH_CARD)

    def test_pair(self):
        table, hole = make_cards("Kh Qh Jh", hole="Ah As")
        hand_score = find_best_hand(table, hole)
        self.assertEqual(hand_score.rank, HandRank.PAIR)

    def test_two_pairs(self):
        table, hole = make_cards("Qh", hole="Ah As Kh Ks")
        hand_score = find_best_hand(table, hole)
        self.assertEqual(hand_score.rank, HandRank.TWO_PAIR)

    def test_three_of_a_kind(self):
        table, hole = make_cards("Kh Qh", hole="Ah As Ah")
        hand_score = find_best_hand(table, hole)
        self.assertEqual(hand_score.rank, HandRank.THREE_OF_A_KIND)

    def test_straight(self):
        table, hole = make_cards("9h 8c 7d", hole="6s 5h")
        hand_score = find_best_hand(table, hole)
        self.assertEqual(hand_score.rank, HandRank.STRAIGHT)

    def test_flush(self):
        table, hole = make_cards("Kh Qh Jh 9h", hole="Ah")
        hand_score = find_best_hand(table, hole)
        self.assertEqual(hand_score.rank, HandRank.FLUSH)

    def test_full_house(self):
        table, hole = make_cards("Kh Ks", hole="Ah As Ah")
        hand_score = find_best_hand(table, hole)
        self.assertEqual(hand_score.rank, HandRank.FULL_HOUSE)

    def test_four_of_a_kind(self):
        table, hole = make_cards("Kh", hole="Ah As Ah Ah")
        hand_score = find_best_hand(table, hole)
        self.assertEqual(hand_score.rank, HandRank.FOUR_OF_A_KIND)

    def test_straight_flush(self):
        table, hole = make_cards("9h 8h 7h", hole="6h 5h")
        hand_score = find_best_hand(table, hole)
        self.assertEqual(hand_score.rank, HandRank.STRAIGHT_FLUSH)

    def test_royal_flush(self):
        table, hole = make_cards("Kh Qh Jh Th", hole="Ah")
        hand_score = find_best_hand(table, hole)
        self.assertEqual(hand_score.rank, HandRank.ROYAL_FLUSH)

    def test_histogram_creation(self):
        table, _ = make_cards("Ah As Kh Qh Jh")
        histogram = create_histogram(table)
        self.assertEqual(histogram[Rank.ACE], 2)
        self.assertEqual(histogram[Rank.KING], 1)
        self.assertEqual(histogram[Rank.QUEEN], 1)
        self.assertEqual(histogram[Rank.JACK], 1)

    def test_high_card_score(self):
        table, _ = make_cards("Kh Ah Qh Jh Th")
        score = get_high_card_score(table)
        self.assertEqual(score, (14, 13, 12, 11, 10))

    def test_flush_not_straight(self):
        table, hole = make_cards("4h 8s As Qs 6d", hole="Ks 5s")
        hand_score = find_best_hand(table, hole)
        self.assertEqual(hand_score.rank, HandRank.FLUSH)

    def test_wheel_straight(self):
        table, hole = make_cards("2c 3d 4h", hole="Ah 5h")
        hand_score = find_best_hand(table, hole)
        self.assertEqual(hand_score.rank, HandRank.STRAIGHT)

    def test_ace_low_straight_flush(self):
        table, hole = make_cards("2h 3h 4h", hole="Ah 5h")
        hand_score = find_best_hand(table, hole)
        self.assertEqual(hand_score.rank, HandRank.STRAIGHT_FLUSH)

    def test_multiple_possible_hands(self):
        table, hole = make_cards("Ac Kh Ks Qh Qs", hole="Ah As")
        hand_score = find_best_hand(table, hole)
        self.assertEqual(hand_score.rank, HandRank.FULL_HOUSE)

    def test_high_card_comparison(self):
        table1, hole1 = make_cards("Ks Qh Js 9h", hole="Ah")
        table2, hole2 = make_cards("Kh Qs Jh 8h", hole="As")
        score1 = find_best_hand(table1, hole1)
        score2 = find_best_hand(table2, hole2)
        self.assertGreater(score1.high_card_score, score2.high_card_score)

    def test_pair_comparison(self):
        table1, hole1 = make_cards("Kh Qh Jh", hole="Ah As")
        table2, hole2 = make_cards("Kh Qh Th", hole="Ah As")
        score1 = find_best_hand(table1, hole1)
        score2 = find_best_hand(table2, hole2)
        self.assertGreater(score1.high_card_score, score2.high_card_score)

    def test_two_pair_comparison(self):
        table1, hole1 = make_cards("Qh", hole="Ah As Kh Ks")
        table2, hole2 = make_cards("Qh", hole="Ah As Kh Ks Jh")
        score1 = find_best_hand(table1, hole1)
        score2 = find_best_hand(table2, hole2)
        self.assertEqual(score1.high_card_score, score2.high_card_score)

    def test_three_of_a_kind_comparison(self):
        table1, hole1 = make_cards("Kh Qh", hole="Ah As Ah")
        table2, hole2 = make_cards("Kh Jh", hole="Ah As Ah")
        score1 = find_best_hand(table1, hole1)
        score2 = find_best_hand(table2, hole2)
        self.assertGreater(score1.high_card_score, score2.high_card_score)

    def test_straight_comparison(self):
        table1, hole1 = make_cards("Qh Jh Th 9h", hole="Kh")
        table2, hole2 = make_cards("Jh Th 9h 8h", hole="Qh")
        score1 = find_best_hand(table1, hole1)
        score2 = find_best_hand(table2, hole2)
        self.assertGreater(score1.high_card_score, score2.high_card_score)

    def test_flush_comparison(self):
        table1, hole1 = make_cards("Kh Qh Jh Th", hole="Ah")
        table2, hole2 = make_cards("Qh Jh Th 9h", hole="Kh")
        score1 = find_best_hand(table1, hole1)
        score2 = find_best_hand(table2, hole2)
        self.assertGreater(score1.high_card_score, score2.high_card_score)

    def test_full_house_comparison(self):
        table1, hole1 = make_cards("Kh Ks", hole="Ah As Ah")
        table2, hole2 = make_cards("Ah As", hole="Kh Ks Kh")
        score1 = find_best_hand(table1, hole1)
        score2 = find_best_hand(table2, hole2)
        self.assertGreater(score1.high_card_score, score2.high_card_score)

    def test_four_of_a_kind_comparison(self):
        table1, hole1 = make_cards("Kh", hole="Ah As Ah Ah")
        table2, hole2 = make_cards("Qh", hole="Ah As Ah Ah")
        score1 = find_best_hand(table1, hole1)
        score2 = find_best_hand(table2, hole2)
        self.assertGreater(score1.high_card_score, score2.high_card_score)

    def test_straight_flush_comparison(self):
        table1, hole1 = make_cards("Qh Jh Th 9h", hole="Kh")
        table2, hole2 = make_cards("Jh Th 9h 8h", hole="Qh")
        score1 = find_best_hand(table1, hole1)
        score2 = find_best_hand(table2, hole2)
        self.assertGreater(score1.high_card_score, score2.high_card_score)

    def test_royal_flush_vs_straight_flush(self):
        table1, hole1 = make_cards("Ks Qs Js Ts", hole="As")
        table2, hole2 = make_cards("Qs Js Ts 9s", hole="Ks")
        score1 = find_best_hand(table1, hole1)
        score2 = find_best_hand(table2, hole2)
        self.assertGreater(score1.rank, score2.rank)

    def test_flush_must_keep_suit(self):
        table, hole = make_cards("3h 4h 5h 7h As", hole="2h 9c")
        score = find_best_hand(table, hole)
        self.assertEqual(score.rank, HandRank.FLUSH)
        self.assertTrue(all(c.suit == Suit.HEARTS for c in score.cards))

    def test_full_house_double_trips(self):
        table, hole = make_cards("3c 3d 3s 2c 2d", hole="2s Kh")
        score = find_best_hand(table, hole)
        self.assertEqual(score.rank, HandRank.FULL_HOUSE)
        ranks = [c.rank for c in score.cards]
        self.assertEqual(ranks.count(Rank.THREE), 3)
        self.assertEqual(ranks.count(Rank.TWO), 2)

    def test_wheel_straight_flush(self):
        table, hole = make_cards("Ah Kh 5h 4h 3h", hole="2h Tc")
        score = find_best_hand(table, hole)
        self.assertEqual(score.rank, HandRank.STRAIGHT_FLUSH)

    def test_high_card_with_score(self):
        table, hole = make_cards("As Kh 7d 4c 2s", hole="Jc 9h")
        score = find_best_hand(table, hole)
        self.assertEqual(score.rank, HandRank.HIGH_CARD)
        self.assertEqual(score.high_card_score, (14, 13, 11, 9, 7))

    def test_two_pair_board_pair_in_hole(self):
        table, hole = make_cards("5c 5d Ks 8h 2h", hole="Kh 8c")
        score = find_best_hand(table, hole)
        self.assertEqual(score.rank, HandRank.TWO_PAIR)
        self.assertEqual(score.high_card_score, (13, 13, 8, 8, 5))

    def test_pair_and_kicker_order(self):
        table, hole = make_cards("5c 5d Ks 8h 2h", hole="Kh 9c")
        score = find_best_hand(table, hole)
        self.assertEqual(score.rank, HandRank.TWO_PAIR)
        self.assertEqual(score.high_card_score, (13, 13, 9, 8, 5))

    def test_three_of_kind_vs_full_house(self):
        table, hole = make_cards("7s 7h 7d Kc 2c", hole="Kd 2d")
        score = find_best_hand(table, hole)
        self.assertEqual(score.rank, HandRank.FULL_HOUSE)
        self.assertEqual(score.high_card_score, (13, 13, 7, 7, 7))

    def test_wheel_straight_with_score(self):
        table, hole = make_cards("Ah 2c 3d 4h 5s", hole="9c Jh")
        score = find_best_hand(table, hole)
        self.assertEqual(score.rank, HandRank.STRAIGHT)
        self.assertEqual(score.high_card_score, (5, 4, 3, 2, 14))

    def test_straight_flush_and_royal_flush_priority(self):
        table1, hole1 = make_cards("Ks Qs Js Ts 9s", hole="As 2s")
        table2, hole2 = make_cards("Ks Qs Js Ts 9s", hole="8s 7s")
        score1 = find_best_hand(table1, hole1)
        score2 = find_best_hand(table2, hole2)
        self.assertEqual(score1.rank, HandRank.ROYAL_FLUSH)
        self.assertEqual(score2.rank, HandRank.STRAIGHT_FLUSH)
        self.assertGreater(score1.rank, score2.rank)

if __name__ == '__main__':
    unittest.main() 