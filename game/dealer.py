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
from detector import sortCards,findHandValue
import random


class Dealer(object):
    def __init__(self):
        self.deck = []
        self.players = []
        self.tableCards = []
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

    def shuffle(self):
        for i in range(len(self.deck)-1 , 0, -1):
            rand = random.randint(0,i)
            self.deck[i], self.deck[rand]= self.deck[rand], self.deck[i]
        return self

    def drawCard(self):
        return self.deck.pop()


    def round(self):
        """
        Questions every player which option will be choosen
        :returns: TODO

        """
        for i in self.players:
            diff = i.options()
            if diff:
                self.players[self.players.index(i)+1].diff = diff 
        return self
            
    def dealCard(self):
        """
        Deals cards to everyone
        :returns: self

        """
        for i in self.players:
            i.hand.append(self.drawCard())
        return self 


    def drawTable(self):
        """
        Draw a card on table
        :returns: TODO

        """
        self.tableCards.append(self.drawCard())
        return self

    def listCards(self, player):
        """
        Creates the list of cards for specific player

        :player: object Player()
        :returns: list of cards on table and hand of specific player

        """
        return self.tableCards + player.hand

    def clearCards(self):
        """
        Clear all played cards
        :returns: TODO

        """
        self.tableCards = []
        for index,player in enumerate(self.players):
            self.players[index].hand = []
        return self
  
    def cleanPlayers(self):
        for index,player in enumerate(self.players[:]):
            if player.money == 0:
                self.players.remove(player)
    
    
    def addPlayer(self,player):
        self.players.append(player)
        return self


    def createPlayers(self,name,numPlayers=2,money=500.0, difficulty="easy"):
        self.addPlayer(player.Player(name,money))
        for i in range(1,numPlayers+1):
            if difficulty == "easy":
               self.addPlayer(player.EasyBot())
               self.players[i].name +=str(i)
        return self

    def listPlayingCards(self, cards):
        """
        Lists the players working cards (Player's hand + kickers)

        :cards: TODO
        :returns: best possible hand with kickers

        """
        kickers = sorted(self.tableCards, key = lambda a: a[0], reverse = True)
        return (cards + kickers)[:5] 
        #  change it to the detector function for finding best high card possible:  <26-08-19>, dave> 
        #  update sorting so it can sort through all cards:  <26-08-19, yourname> # 
    def calculateHandValues(self, players):
        """
        Creates a list of hand values of everybody playing

        :players: TODO
        :returns: TODO

        """
        for player in players:
            cards = sortCards(self.listCards(player))
            player.handValue = findHandValue(cards)
        return players

    def chooseWinner(self, players):
        """
        Decides who wins the prize by sorting players by their handValues

        :players: TODO
        :returns: winning player, or list of players if more then one

        """
        players = self.calculateHandValues(players)
        for player in players:
            print(player.name, player.handValue)
        players = sorted(players, key = lambda x: x.handValue, reverse = True)
        #players.sort(reverse = True) #get lambda to sort by hand value attribute 
        winners = [players[0]]
        for player in players[1:]:
            if player.handValue != winners[0].handValue:
                break
            else:
                winners.append(player)
        return winners

    def givePot(self,players):
        """
        Gives the pot to the winner(s)
        :returns: TODO

        """
        prize = self.pot/len(players)
        for i in players:
            i.money += prize
        self.pot = 0.0
    
