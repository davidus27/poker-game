"""
File: detector.py
Author: dave
Github: https://github.com/davidus27
Description: Class for easier detection of all existing hand values of players.
"""
class Detector(object):
     
    suits = {"Spades" : "♠" , "Clubs" : "♣" , "Diamonds" : "♦" , "Hearts": "♥"}
    #numericalValues = {"Jack":11, "Queen":12, "King":13, "Ace":14}
    cardsOrder = [2,3,4,5,6,7,8,9,10, "Jack", "Queen" , "King", "Ace"]

    def __init__(self):
        pass


    def createHistogram(self, cards):
        """
        Creates histogram of hole and community cards

        :cards: TODO
        :returns: dictionary of used cards 

        """ 
        d = {}
        for i in cards:
            if i[0] not in d:
                d[i[0]] =0
            else:
                d[i[0]] +=1

        return d


   def pair(self, cards):
        """
        Checks if the dictionary has ONE pair
        Calculates cardValue of hand
        :returns: value of hand
        """
        d = self.createHistogram(cards)
        pack = []
        for i in d:
            if d[i] == 1:
                for j in cards:
                    if j[0] == i:
                        pack.append(j)
                return pack
        return False
    
