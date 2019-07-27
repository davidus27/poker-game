#!/usr/bin/python
# vim: set fileencoding=utf-8 :
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
    
    def twoPairs(self,cards):
        """
        Two different pairs
        :returns: TODO

        """
        count = 0
        for i in cards:
            if cards[i] == 1:
                count += 1
        if count == 2:
            return True
        return False



    def threeOfKind(self, cards):
        """
        Finds Three of a kind (Three cards with same value)
        :cards: dictionary of hole and community cards
        :returns: boolean

        """
        for i in cards:
            if cards[i] == 2:
                return True

        return False
      

    def fourOfKind(self, cards):
        """
        Finds Four of a kind (four cards with same value)

        :cards: dictionary
        :returns: boolean

        """
        for i in cards:
            if cards[i] == 3:
                return True
        return False


    def straight(self,cards):
        """
        Five cards in order
        :returns: TODO

        """
        pack = []
        cards = self.sortCards(cards)
        for index,card in enumerate(cards):
            if len(pack) == 4:
                pack.append(card)
                return pack            
            control = self.cardsOrder.index(card[0]) - self.cardsOrder.index(cards[index+1][0])
            if control == 1:        
                pack.append(card)
            elif control == 0:
                continue
            else:
                return False



    def sortCards(self, cards):
        """
        Sort cards from highest based on values

        :cards: TODO
        :returns: TODO

        """
        return sorted(cards, key = lambda a: (self.cardsOrder.index(a[0]), a[1]), reverse=True)
   
    def flush(self,cards):
        """
        Five cards of the same suit
        :returns: TODO

        """
        #it will lookup the biggest flush in cards
        cards = self.sortCards(cards)
        
        for i in self.suits:
            pack=[]
            for j in cards:
                if j[1] is i:
                    pack.append(j)
                if len(pack) >= 5:
                    return pack
        return False


    def fullHouse(self,cards):
        """
        A pair and 3 of a kind
        :returns: TODO

        """
        x,y = 0,0
        for i in cards:
            if cards[i] == 1:
                x += 1
            elif cards[i] == 2:
                y += 1
        if x == 1 and y ==1:
            return True
        return False


    def straightFlush(self,cards):
        """
        Straight and flush
        :returns: TODO

        """
        # not functioning properly:  <25-07-19, dave> #
        flush = self.flush(cards)
        straight = self.straight(cards)
        if straight == flush:
            return straight
        return False

    def royalFlush(self,cards):
        """
        The highest cards on hand. 
        all of the same color: 10,jack,queen, king, ace 
        :returns: TODO

        """
        royal = [10, "Jack", "Queen", "King", "Ace"]
        flush = self.flush(cards)
        if flush:    
            for i in flush:
                if i[0] not in royal:
                    return False
            return True
        return False
