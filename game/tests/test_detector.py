import unittest
from dealer.detector import (
    find_best_hand, high_card_score, create_histogram
)
from cards import Card, Suit, Rank

class TestPokerHandDetector(unittest.TestCase):
    def setUp(self):
        # Define some test cards using the new Card class
        self.ace_hearts = Card(Rank.ACE, Suit.HEARTS)
        self.king_hearts = Card(Rank.KING, Suit.HEARTS)
        self.queen_hearts = Card(Rank.QUEEN, Suit.HEARTS)
        self.jack_hearts = Card(Rank.JACK, Suit.HEARTS)
        self.ten_hearts = Card(Rank.TEN, Suit.HEARTS)
        self.nine_hearts = Card(Rank.NINE, Suit.HEARTS)
        self.eight_hearts = Card(Rank.EIGHT, Suit.HEARTS)
        self.seven_hearts = Card(Rank.SEVEN, Suit.HEARTS)
        self.six_hearts = Card(Rank.SIX, Suit.HEARTS)
        self.five_hearts = Card(Rank.FIVE, Suit.HEARTS)
        self.four_hearts = Card(Rank.FOUR, Suit.HEARTS)
        self.three_hearts = Card(Rank.THREE, Suit.HEARTS)
        self.two_hearts = Card(Rank.TWO, Suit.HEARTS)
        
        # Different suits
        self.ace_spades = Card(Rank.ACE, Suit.SPADES)
        self.king_spades = Card(Rank.KING, Suit.SPADES)
        self.queen_spades = Card(Rank.QUEEN, Suit.SPADES)
        self.jack_spades = Card(Rank.JACK, Suit.SPADES)
        self.ten_spades = Card(Rank.TEN, Suit.SPADES)

    def test_high_card(self):
        cards = [self.ace_hearts, self.king_spades, self.queen_hearts, self.jack_spades, self.nine_hearts]
        value = find_best_hand(cards)
        self.assertGreater(value, 0)  # Should be greater than 0
        self.assertLess(value, 1)     # Should be less than 1 (pair value)

    def test_pair(self):
        cards = [self.ace_hearts, self.ace_spades, self.king_hearts, self.queen_hearts, self.jack_hearts]
        value = find_best_hand(cards)
        self.assertGreater(value, 1)  # Should be greater than 1
        self.assertLess(value, 2)     # Should be less than 2 (two pairs value)

    def test_two_pairs(self):
        cards = [self.ace_hearts, self.ace_spades, self.king_hearts, self.king_spades, self.queen_hearts]
        value = find_best_hand(cards)
        self.assertGreater(value, 2)  # Should be greater than 2
        self.assertLess(value, 3)     # Should be less than 3 (three of a kind value)

    def test_three_of_a_kind(self):
        cards = [self.ace_hearts, self.ace_spades, self.ace_hearts, self.king_hearts, self.queen_hearts]
        value = find_best_hand(cards)
        self.assertGreater(value, 3)  # Should be greater than 3
        self.assertLess(value, 4)     # Should be less than 4 (straight value)

    def test_straight(self):
        cards = [
            Card(Rank.NINE, Suit.HEARTS),
            Card(Rank.EIGHT, Suit.CLUBS),
            Card(Rank.SEVEN, Suit.DIAMONDS),
            Card(Rank.SIX, Suit.SPADES),
            Card(Rank.FIVE, Suit.HEARTS)
        ]
        value = find_best_hand(cards)
        self.assertGreater(value, 4)  # Should be greater than 4
        self.assertLess(value, 5)     # Should be less than 5 (flush value)

    def test_flush(self):
        cards = [self.ace_hearts, self.king_hearts, self.queen_hearts, self.jack_hearts, self.nine_hearts]
        value = find_best_hand(cards)
        self.assertGreater(value, 5)  # Should be greater than 5
        self.assertLess(value, 6)     # Should be less than 6 (full house value)

    def test_full_house(self):
        cards = [self.ace_hearts, self.ace_spades, self.ace_hearts, self.king_hearts, self.king_spades]
        value = find_best_hand(cards)
        self.assertGreater(value, 6)  # Should be greater than 6
        self.assertLess(value, 7)     # Should be less than 7 (four of a kind value)

    def test_four_of_a_kind(self):
        cards = [self.ace_hearts, self.ace_spades, self.ace_hearts, self.ace_hearts, self.king_hearts]
        value = find_best_hand(cards)
        self.assertGreater(value, 7)  # Should be greater than 7
        self.assertLess(value, 8)     # Should be less than 8 (straight flush value)

    def test_straight_flush(self):
        cards = [
            Card(Rank.NINE, Suit.HEARTS),
            Card(Rank.EIGHT, Suit.HEARTS),
            Card(Rank.SEVEN, Suit.HEARTS),
            Card(Rank.SIX, Suit.HEARTS),
            Card(Rank.FIVE, Suit.HEARTS)
        ]
        value = find_best_hand(cards)
        self.assertGreater(value, 8)  # Should be greater than 8
        self.assertLess(value, 9)     # Should be less than 9 (royal flush value)

    def test_royal_flush(self):
        cards = [self.ace_hearts, self.king_hearts, self.queen_hearts, self.jack_hearts, self.ten_hearts]
        value = find_best_hand(cards)
        self.assertEqual(value, 9)    # Should be exactly 9 (royal flush value)

    def test_histogram_creation(self):
        cards = [self.ace_hearts, self.ace_spades, self.king_hearts, self.queen_hearts, self.jack_hearts]
        histogram = create_histogram(cards)
        self.assertEqual(histogram[Rank.ACE], 2)
        self.assertEqual(histogram[Rank.KING], 1)
        self.assertEqual(histogram[Rank.QUEEN], 1)
        self.assertEqual(histogram[Rank.JACK], 1)

    def test_high_card_score(self):
        cards = [self.king_hearts, self.ace_hearts, self.queen_hearts, self.jack_hearts, self.ten_hearts]
        score = high_card_score(cards)
        self.assertGreater(score, 0)
        self.assertLess(score, 1)

    def test_flush_not_straight(self):
        community_cards = [
            Card(Rank.FOUR, Suit.HEARTS),
            Card(Rank.EIGHT, Suit.SPADES),
            Card(Rank.ACE, Suit.SPADES),
            Card(Rank.QUEEN, Suit.SPADES),
            Card(Rank.SIX, Suit.DIAMONDS)
        ]
        player_cards = [
            Card(Rank.KING, Suit.SPADES),
            Card(Rank.FIVE, Suit.SPADES)
        ]
        all_cards = community_cards + player_cards
        value = find_best_hand(all_cards)
        self.assertGreater(value, 5)  # Should be greater than 5 (flush value)
        self.assertLess(value, 6)     # Should be less than 6 (full house value)

if __name__ == '__main__':
    unittest.main() 