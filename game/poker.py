"""
File: poker.py
Author: dave
Github: https://github.com/davidus27
Description: Game is the main Object implementing all the necessary tools for playing. Game is created in function main()
                        RUNS THE WHOLE PROGRAM!
"""
import dealer
import printouts 

class Game(object):
    """
    Creates players based on inputs on call.
    """
    def __init__(self):
        self.player = None
        self.players = []
        self.info = printouts.PrintOuts()
        self.dealer = dealer.Dealer(self.info.numPlayers)

