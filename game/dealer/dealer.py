"""
File: dealer.py
Author: yourname
Email: yourname@email.com
Github: https://github.com/yourname
Description: This is elementary class for maintaining players and cards in the game
"""

from dealer.cardControl import CardControl
from dealer.playerControl import PlayerControl

class Dealer(object):

    """This class will maintain players and cards"""

    def __init__(self):
        self.cardControl = CardControl()
        self.playerControl = PlayerControl()

    def giveCards(self):
        """
        gives cards.
        :returns: TODO

        """
        self.cardControl.dealCard(self.playerControl.players)
        self.cardControl.dealCard(self.playerControl.players)
 
    def gameOn(self):
        """
        Clears all the cards, create cards and shuffles them
        :returns: TODO

        """
        self.cardControl.buildDeck()
        self.cardControl.shuffle()
        return self

    def endGame(self):
        """
        Clear players list, removes debt and recreates deck

        :returns: TODO

        """
        self.cardControl.deck = []
        self.cardControl.clearCards(self.playerControl.players)
        self.playerControl.cleanPlayers() 
        self.playerControl.clearPlayersDebt()
        return self

    def cardOnTable(self, phase):
        """
        Three cards on table while flop
        :returns: TODO

        """
        if phase == "Preflop":
            self.cardControl.drawTable()
            self.cardControl.drawTable()
            self.cardControl.drawTable()

        elif phase == "Flop" or phase == "River":
            self.cardControl.drawTable()
        elif phase == "Turn":
            pass

        elif phase == "All-flop":
            self.cardControl.drawTable()
            self.cardControl.drawTable()

        elif phase == "All-turn":
            self.cardControl.drawTable()
        return True



    def chooseWinner(self, players):
        """
        Decides who wins the prize by sorting players by their handValues

        :players: TODO
        :returns: winning player, or list of players if more then one

        """
        #calculate hand values to everyone
        players = self.cardControl.calculateHandValues(players)

        for player in players:
            print(player.name, ":", player.handValue)
        #sort players by hand value
        players = sorted(players, key = lambda x: x.handValue, reverse = True)
        #first is the winner
        winners = [players[0]]
        #check if there is more than one winner, 
        #if there is return the list of players
        for player in players[1:]:
            if player.handValue != winners[0].handValue:
                break
            else:
                winners.append(player)
        return winners
