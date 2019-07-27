#!/usr/bin/python
# vim: set fileencoding=utf-8 :

"""
File: dealer.py
Author: dave
Github: https://github.com/davidus27
Description: We need to create a "Dealer" for a game so we can 
    easily manage a pot (money on a table) cards on a table, cards on hands,shuffling and who wins.
"""


import player
import detector
import random


class Dealer(object):
    def __init__(self,numPlayers):
        self.deck = []
        self.players = []
        self.tableCards = []
        self.numPlayers = numPlayers
        self.pot = 0

    def buildDeck(self):
        """
        Creates list of cards.
        Individual cards are tuples with format: (number,color)
        """
        colors = ["Spades" , "Clubs", "Diamonds", "Hearts"]
        numbers = [2, 3, 4, 5, 6 ,7 ,8 , 9 ,10,"Jack", "Queen","King", "Ace"]
        for color in colors:
            for number in numbers:
                self.deck.append((number,color))
        return self
