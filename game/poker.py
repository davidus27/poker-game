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

    def giveCards(self):
        """
        gives cards.
        :returns: TODO

        """
        self.dealer.dealCard()
        self.dealer.dealCard()
        self.dealer.drawTable()
        self.dealer.drawTable()
        self.dealer.drawTable()

def main():
    """ 
    Work to create game
    """

    game = Game()
    game.askQuestions()

    game.createPlayers()
    game.giveCards()

    game.dealer.drawTable()
    game.dealer.drawTable()


    det = detector.Detector()
       
    for i in game.dealer.players:
        #cards = game.dealer.listCards(i)
        cards = det.sortCards(game.dealer.listCards(i))
        histogram = det.createHistogram(cards)
        
        print(i.name)
        print(cards)
        print("pair: ", det.pair(histogram, cards))
        print("two pairs: ", det.twoPairs(histogram, cards))
        print("Three of a kind:" , det.threeOfKind(histogram, cards))
        print("Four of a kind:" , det.fourOfKind(histogram, cards))
        print("Straight: ", det.straight(cards))
        print("Flush: ", det.flush(cards))
        print("Full house: ", det.fullHouse(histogram, cards))
        print("StraightFlush: ", det.straightFlush(cards))
        print("RoyalFlush: ", det.royalFlush(cards))
        print("Final Countdown: ", game.dealer.findHandValue(i))
        print("High card: ", det.highCard(cards))
        print()



if __name__ == "__main__":
    main()

