from typing import Dict
from dealer.detector import HandScore, HandRank

HAND_NAMES: Dict[HandRank, str] = {
    HandRank.HIGH_CARD: "High Card",
    HandRank.PAIR: "Pair",
    HandRank.TWO_PAIR: "Two Pairs",
    HandRank.THREE_OF_A_KIND: "Three of a Kind",
    HandRank.STRAIGHT: "Straight",
    HandRank.FLUSH: "Flush",
    HandRank.FULL_HOUSE: "Full House",
    HandRank.FOUR_OF_A_KIND: "Four of a Kind",
    HandRank.STRAIGHT_FLUSH: "Straight Flush",
    HandRank.ROYAL_FLUSH: "Royal Flush"
}

def print_hand_value(hand_score: HandScore) -> None:
    """
    Prints the value of the player's hand in a human-readable format.
    
    Args:
        hand_score: The HandScore object containing the hand's rank and details
    """
    print(HAND_NAMES[hand_score.rank])


