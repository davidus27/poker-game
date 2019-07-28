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



    def options(self, action):
        """
        Gives all options to the player
        :action: input of the player
        :returns: used function

        """
        pass


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
