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


    def createPlayers(self):
        player = self.dealer.firstPlayer(self.info.name, self.info.money)
        self.dealer.createPlayers(player)
        return self


def main():
    """ 
    Work to create game
    """

    game = Game()
    game.createPlayers()




if __name__ == "__main__":
    main()

