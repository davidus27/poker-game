from enum import Enum, auto
from dataclasses import dataclass

class Suit(Enum):
    HEARTS = auto()
    DIAMONDS = auto()
    CLUBS = auto()
    SPADES = auto()

    def __str__(self):
        return self.name.capitalize()

class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    def __str__(self):
        return self.name.capitalize()

@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    # let's add the ascii art for the cards
    suits = {"Spades" : "♠" , "Clubs" : "♣" , "Diamonds" : "♦" , "Hearts": "♥"}
