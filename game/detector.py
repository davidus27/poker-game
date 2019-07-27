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


    """
    All possible hand values checkers:

        0) Highcard: Simple value of the card.

        1) Pair: Two cards with same value.

        2) Two pairs: Two different pairs.
        
        3) Three of a Kind: Three cards with the same value
        
        4) Straight: Sequence of five cards in increasing value (Ace can precede two and follow up King)
        
        5) Flush: Five cards of the same suit
        
        6) Full House: Combination of three of a kind and a pair
        
        7) Four of a kind: Four cards of the same value
        
        8) Straight flush: Straight of the same suit
        
        9) Royal Flush: Straight flush from Ten to Ace


    The value of hand will get number based on the sequence above
        (Pair will get 1, Straight will get 4 and so on) 
    
    Highcard will enumerate decimal places so if two players will have same hand the higher cards will win.

    """

    def createHistogram(self, cards):
        """
        Creates histogram of hole and community cards

        :cards: TODO
        :returns: histogramictionary of used cards 

        """ 
        histogram = {}
        for i in cards:
            if i[0] not in histogram:
                histogram[i[0]] =0
            else:
                histogram[i[0]] +=1

        return histogram


    def pair(self, histogram):
        """
        Checks if the dictionary has ONE pair
        Calculates cardValue of hand
        :returns: value of hanhistogram
        """
        for i in histogram:
            if histogram[i] == 1:
                return True

        return False


    
    def twoPairs(self,histogram):
        """
        Two different pairs
        :returns: TODO

        """
        count = 0
        for i in histogram:
            if histogram[i] == 1:
                count += 1
        if count == 2:
            return True
        return False



    def threeOfKind(self, histogram):
        """
        Finds Three of a kind (Three histogram with same value)
        :histogram: dictionary of hole and community histogram
        :returns: boolean

        """
        for i in histogram:
            if histogram[i] == 2:
                return True

        return False
      

    def fourOfKind(self, histogram):
        """
        Finds Four of a kind (four histogram with same value)

        :histogram: dictionary
        :returns: boolean

        """
        for i in histogram:
            if histogram[i] == 3:
                return True
        return False


    def straight(self, cards):
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


    def fullHouse(self,histogram):
        """
        A pair and 3 of a kind
        :returns: TODO

        """
        x,y = 0,0
        for i in histogram:
            if histogram[i] == 1:
                x += 1
            elif histogram[i] == 2:
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
