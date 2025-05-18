import unittest
from io import StringIO
from contextlib import redirect_stdout
from dealer.detector import HandScore, HandRank
from ui.cli.printResults import print_hand_value

class TestPrintResults(unittest.TestCase):
    def setUp(self):
        self.output = StringIO()

    def test_print_high_card(self):
        with redirect_stdout(self.output):
            print_hand_value(HandScore(HandRank.HIGH_CARD, 0, []))
        self.assertEqual(self.output.getvalue().strip(), "High Card")

    def test_print_pair(self):
        with redirect_stdout(self.output):
            print_hand_value(HandScore(HandRank.PAIR, 0, []))
        self.assertEqual(self.output.getvalue().strip(), "Pair")

    def test_print_two_pairs(self):
        with redirect_stdout(self.output):
            print_hand_value(HandScore(HandRank.TWO_PAIR, 0, []))
        self.assertEqual(self.output.getvalue().strip(), "Two Pairs")

    def test_print_three_of_a_kind(self):
        with redirect_stdout(self.output):
            print_hand_value(HandScore(HandRank.THREE_OF_A_KIND, 0, []))
        self.assertEqual(self.output.getvalue().strip(), "Three of a Kind")

    def test_print_straight(self):
        with redirect_stdout(self.output):
            print_hand_value(HandScore(HandRank.STRAIGHT, 0, []))
        self.assertEqual(self.output.getvalue().strip(), "Straight")

    def test_print_flush(self):
        with redirect_stdout(self.output):
            print_hand_value(HandScore(HandRank.FLUSH, 0, []))
        self.assertEqual(self.output.getvalue().strip(), "Flush")

    def test_print_full_house(self):
        with redirect_stdout(self.output):
            print_hand_value(HandScore(HandRank.FULL_HOUSE, 0, []))
        self.assertEqual(self.output.getvalue().strip(), "Full House")

    def test_print_four_of_a_kind(self):
        with redirect_stdout(self.output):
            print_hand_value(HandScore(HandRank.FOUR_OF_A_KIND, 0, []))
        self.assertEqual(self.output.getvalue().strip(), "Four of a Kind")

    def test_print_straight_flush(self):
        with redirect_stdout(self.output):
            print_hand_value(HandScore(HandRank.STRAIGHT_FLUSH, 0, []))
        self.assertEqual(self.output.getvalue().strip(), "Straight Flush")

    def test_print_royal_flush(self):
        with redirect_stdout(self.output):
            print_hand_value(HandScore(HandRank.ROYAL_FLUSH, 0, []))
        self.assertEqual(self.output.getvalue().strip(), "Royal Flush") 