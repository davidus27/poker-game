"""
File:player.py
Author:dave
Github:https://github.com/davidus27
Description:Player and variations of bots.
"""
from random import random
from printouts import optionsInput

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
       print("{} call".format(self.name))
       #if self.money > self.diff:
       #    self.money -= self.diff
       #else:
       #    return True
       return True
    def raiseBet(self):
       """
       Method for raising bets

       :diff: the amount to call
       :raising: amount to 
       """
       print("{} raiseBet!".format(self.name))
       return True

    def checkBet(self):
       """
       Checks only if diff is zero

       :diff: difference between bets
       :returns: True/False based on if you can check or not

       """
       print("{} check".format(self.name))
       return bool(self.diff)

    def foldBet(self):
       """
       :returns: self

       """
       print("{} fold.".format(self.name))
       return True


    def allIn(self):
       """
       Gives all money to the pot

       :currentBet: Money on pot
       :returns: currentBet with all player's money

       """
       #currentBet += self.money
       print("{} all in!".format(self.name))
       return money
    
    def options(self):
        """
        Gives all options to the player
        :action: input of the player
        :returns: used function

        """
        action = optionsInput()
        options = {1: self.checkBet ,
                    2: self.callBet , 
                    3: self.raiseBet , 
                    4: self.foldBet , 
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


    def options(self):
        """
        Gives all options to the player
        :action: input of the player
        :returns: used function

        """
        options = {1: self.checkBet ,
                    2: self.callBet , 
                    3: self.raiseBet , 
                    4: self.foldBet , 
                    5: self.allIn,
                    }
        while True:
            x = random()
            if x <= 0.05:
                action = 4

            elif x <= 0.45:
                action = 1

            elif x <= 0.85:
                action = 2

            elif x <= 0.995:
                action = 3

            elif x <= 1.0:
                action = 5
            
            choosen = options[action]()
            if choosen:
                return choosen
            else:
                continue

