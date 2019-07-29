"""
File: poker.py
Author: dave
Github: https://github.com/davidus27
Description: Game is the main Object implementing all the necessary tools for playing. Game is created in function main()
                        RUNS THE WHOLE PROGRAM!
"""
import dealer
import printouts

import detector

class Game(object):
    """
    Creates players based on inputs on call.
    """
    def __init__(self, name = "Player0", money = 500.0, difficulty ="easy", numPlayers = 2):
        self.name = name
        self.money = money
        self.difficulty = difficulty
        self.numPlayers = numPlayers
        self.dealer = dealer.Dealer()



    def createPlayers(self):
        self.dealer.createPlayers(numPlayers = self.numPlayers,
                                name = self.name ,
                                money = self.money,
                                difficulty = self.difficulty, )
        return self

    def askQuestions(self):
        """
        Asks the player initial questions
        :returns: TODO

        """
        self.name = printouts.nameQuest()
        self.numPlayers = printouts.numQuest()
        self.difficulty = printouts.diffQuest()

    def giveCards(self):
        """
        gives cards.
        :returns: TODO

        """
        self.dealer.dealCard()
        self.dealer.dealCard()

import time
def main():
    """ 
    Work to create game
    """
    b = time.time()
    game = Game()
    print("Let's play Texas Hold'em!")
    #game.askQuestions()
    game.createPlayers()
    game.giveCards()
    rounds = 1
    while True:
        printouts.info(game.name, game.money, rounds)
        #for player in game.dealer.players:
        #    cards = detector.sortCards(game.dealer.listCards(i))
        #    histogram = detector.createHistogram(cards)
        
        game.dealer.round()
        break

    print(game.dealer.chooseWinner())
 



    print(time.time()-b)

if __name__ == "__main__":
    main()

