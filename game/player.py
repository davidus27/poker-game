"""
File:player.py
Author:dave
Github:https://github.com/davidus27
Description:Player and variations of bots.
"""
from random import random, randint
from printouts import optionsInput, raising
from sys import exit
from os import system

class Player(object):
    def __init__(self, name = "Player", money = 500.0):
        self.name = name
        self.money = money
        self.hand = []
        self.diff = 0.0


    def clearDiff(self):
        """
        Clears diff after operation
        :returns: TODO

        """
        diff = self.diff
        self.diff = 0
        return diff


    def callBet(self):
        """
        Action for player to call a bet on table

        :returns: diff

        """
        if self.diff == 0.0:
            return self.checkBet()
     
        elif self.diff >= self.money:
            return self.allin()
    
        elif self.diff < self.money:
           self.money -= self.diff
           print("{} call".format(self.name))
           return self.clearDiff()

    def raiseBet(self):
       """
       Method for raising bets
       :returns: diff
       """
       while True:  
            raised = raising(self.diff, self.money)
            
            if raised < self.diff:
                print("Too small investment. You need to input more.")
            
            elif raised == self.diff:
                return self.callBet()
            
            elif raised >= self.money:
                return self.allin()

            else:
                self.money -= raised
                print("{} raised bet:{} ".format(self.name,raised))
                return raised - self.clearDiff()

    def checkBet(self):
        """
        Checks only if diff is zero
        
        :returns: True/False based on if you can check or not
        """
        if self.diff:
            print("Cannot perform check.", self.name)
            return False
        else:
            print("{} check".format(self.name))
            return 0.0

    def foldBet(self):
       """
       :returns: self

       """
       print("{} fold.".format(self.name))
       self.hand = []
       return -1,self.clearDiff()

    def allin(self):
       """
       Gives all money to the pot

       :currentBet: Money on pot
       :returns: currentBet with all player's money

       """
       #currentBet += self.money
       print("{} all in!".format(self.name))
       everything = self.money
       self.money = 0
       return everything-self.clearDiff()

    def quit(self):
        print("Exiting program. Hope you will come back again.")
        exit()
    
    def options(self):
        """
        Gives all options to the player
        :action: input of the player
        :returns: used function

        """
        options = { 0: self.quit,
                    1: self.checkBet ,
                    2: self.callBet , 
                    3: self.raiseBet , 
                    4: self.foldBet , 
                    5: self.allin,
                    }
        while True:
            action = optionsInput()
            choosed = options[action]()
            if choosed is not False:
                return choosed
            else:
                continue

class EasyBot(Player):

    """
    Easy to compete player
    Selects randomly between his options
    """

    def __init__(self):
       """TODO: to be defined1. """
       Player.__init__(self)


    def raiseBet(self):
       """
       Method for raising bets

       :diff: the amount to call
       :raising: amount to 
       """
       while True:  
            raised = randint(1,self.money) 
            if raised < self.diff:
                print("Too small investment. You need to input more.")
            elif raised == self.diff:
                return self.checkBet()
            elif raised >= self.money:
                return self.allin()

            else:
                self.money -= raised
                print("{} raised bet:{} ".format(self.name,raised))
                return raised-self.diff

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
                    5: self.allin,
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
            if choosen is not False:
                return choosen
            else:
                continue

