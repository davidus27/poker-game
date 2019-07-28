"""
File:player.py
Author:dave
Github:https://github.com/davidus27
Description:Player and variations of bots.
"""
from random import random

class Player(object):
    def __init__(self, name = "Player", money = 500.0):
        self.name = name
        self.money = money
        self.diff = 0.0
        self.hand = []


    def callBet(self):
       """
       Action for player to call a bet on table

       :returns: TODO

       """
       if self.money > self.diff:
           self.money -= self.diff
       else:
           pass

    def raiseBet(self):
       """
       Method for raising bets

       :diff: the amount to call
       :raising: amount to 
       """
       pass

    def checkBet(self):
       """
       Checks only if diff is zero

       :diff: difference between bets
       :returns: True/False based on if you can check or not

       """
       return bool(diff)

    def foldBet(self):
       """
       :returns: self

       """
       self.hands = []
       self.end()
       return self


    def allIn(self):
       """
       Gives all money to the pot

       :currentBet: Money on pot
       :returns: currentBet with all player's money

       """
       #currentBet += self.money
       money = self.money
       self.money = 0.0
       return money

    def options(self, action):
        """
        Gives all options to the player
        :action: input of the player
        :returns: used function

        """
        pass


    def options(self, action):
        """
        Gives all options to the player
        :action: input of the player
        :returns: used function

        """
        action = PrintOuts().options()
        options = {1: self.checkBet ,
                    2: self.callBet , 
                    3: self.raiseBet , 
                    4: self.fold , 
                    5: self.allIn,
                    }

        return options[action]()




class EasyBot(Player):

    """
    Easy to compete player
    Selects randomly between his options
    """

    def __init__(self):
       """TODO: to be defined1. """
       Player.__init__(self)


    def options(self, action):
        """
        Gives all options to the player
        :action: input of the player
        :returns: used function

        """
        pass
