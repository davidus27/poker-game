from typing import List
from cards import Card, Rank, Suit

# Map Suit Enum to Unicode symbols
SUIT_SYMBOLS = {
    Suit.SPADES: "♠",
    Suit.CLUBS: "♣",
    Suit.DIAMONDS: "♦",
    Suit.HEARTS: "♥"
}

def print_first_line(cards: List[Card]) -> None:
    for _ in cards:
        print("     _______ ", end="")
    print()

def print_second_line(cards: List[Card]) -> None:
    for card in cards:
        print("    ", end="")
        label = get_rank_label(card.rank)
        print(f"|{label:<2}     |", end="")
    print()

def print_middle_line(cards: List[Card]) -> None:
    for card in cards:
        print("    ", end="")
        suit = SUIT_SYMBOLS[card.suit]
        print(f"|   {suit}   |", end="")
    print()

def print_last_line(cards: List[Card]) -> None:
    for card in cards:
        print("    ", end="")
        label = get_rank_label(card.rank)
        print(f"|_____{label:>2}|", end="")
    print()

def get_rank_label(rank: Rank) -> str:
    """
    Returns a short string label for card rank (e.g. 'A' for Ace, 'J' for Jack)
    """
    face_map = {
        Rank.JACK: "J",
        Rank.QUEEN: "Q",
        Rank.KING: "K",
        Rank.ACE: "A"
    }
    return face_map.get(rank, str(rank.value))

def print_cards(cards: List[Card]) -> None:
    """
    Prints the list of Card objects as ASCII-art styled cards in CLI
    """
    print_first_line(cards)
    print_second_line(cards)
    print_middle_line(cards)
    print_middle_line(cards)
    print_middle_line(cards)
    print_last_line(cards)
