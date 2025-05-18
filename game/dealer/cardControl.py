#!/usr/bin/python
# vim: set fileencoding=utf-8 :

"""
File: cardControl.py
Author: dave
Github: https://github.com/davidus27
Description: We need to create a "Dealer" for a game so we can 
    easily manage a pot (money on a table) cards on a table, cards on hands,shuffling and who wins.
"""
from .detector import find_best_hand
from typing import List, Tuple
import random
from cards import Card, Suit, Rank

class CardControl(object):
    
    def __init__(self):
        self.deck = []
        self.tableCards = []


    def buildDeck(self):
        """
        Creates list of cards.
        Individual cards are tuples with format: (number,color)
        """
        for suit in Suit:
            for rank in Rank:
                self.deck.append(Card(rank=rank, suit=suit))
        return self

    def shuffle(self):
        for i in range(len(self.deck)-1 , 0, -1):
            rand = random.randint(0,i)
            self.deck[i], self.deck[rand]= self.deck[rand], self.deck[i]
        return self

    def drawCard(self):
        return self.deck.pop()


    def dealCard(self, players):
        """
        Deals cards to everyone
        :returns: self

        """
        for i in players:
            i.hand.append(self.drawCard())
        return self 


    def drawTable(self):
        """
        Draw a card on table
        :returns: TODO

        """
        self.tableCards.append(self.drawCard())
        return self

    def getAllCards(self, player) -> Tuple[List[Card], List[Card]]:
        """
        Creates the list of cards for specific player

        :player: object Player()
        :returns: list of cards on table and hand of specific player

        """
        return (self.tableCards,  player.hand)

    def clearCards(self, players):
        """
        Clear all played cards
        :returns: TODO

        """
        self.tableCards = []
        for player in players:
            player.hand = []
        return self

    def listPlayingCards(self, player):
        """
        Lists the players working cards (Player's hand + kickers)

        :cards: TODO
        :returns: best possible hand with kickers

        """
        kickers = self.listCards(player)
        return (player.hand + kickers)[:5] 
    
  
    def calculateHandValues(self, players) -> List[Tuple[int, int]]:
        """
        Creates a list of hand values of everybody playing

        :players: TODO
        :returns: TODO

        """
        for player in players:
            player.handValue = find_best_hand(*self.getAllCards(player))
        return players
