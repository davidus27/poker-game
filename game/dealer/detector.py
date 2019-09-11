#!/usr/bin/python
# vim: set fileencoding=utf-8 :
"""
File: detector.py
Author: dave
Github: https://github.com/davidus27
Description: Library for easier detection of all existing hand values of players.
"""

cardsOrder = [2,3,4,5,6,7,8,9,10, "Jack", "Queen" , "King", "Ace"]

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

Card format:
    (number, color)
"""

def createHistogram(cards):
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

def find(cards, value):
    """
    Returns list of cards with same value
    :cards: haystack
    :value: needle
    :returns: needle(s)

    """
    pack = []
    for i in cards:
        if i[0] is value:
            pack.append(i)
    return pack

#  not working correctly change it!:  <23-08-19, yourname> # 
def highCard(cards):
    """
    Finds the high value of cards. From the biggest card to the lowest it increments the decimal place.

    :cards: TODO
    :returns: float

    """
    value = 0.0
    for index,card in enumerate(cards):
        value += 0.01**(index+1) * (cardsOrder.index(card[0]))
    return value

#  override without histogram:  <23-08-19, yourname> # 
def pair(histogram, cards):
    """
    Checks if the dictionary has ONE pair
    Calculates cardValue of hand
    :returns: value of hanhistogram
    """
    for i in histogram:
        if histogram[i] == 1:
            return find(cards, i)

    return False


def twoPairs(histogram, cards):
    """
    Two different pairs
    :returns: TODO

    """
    count = 0
    pack = []
    for i in histogram:
        if histogram[i] == 1:
            pack.append(find(cards, i))
    return pack if len(pack) == 2 else False


def threeOfKind(histogram, cards):
    """
    Finds Three of a kind (Three histogram with same value)
    :histogram: dictionary of hole and community histogram
    :returns: boolean

    """
    for i in histogram:
        if histogram[i] == 2:
            return find(cards,i)
    return False
  

def fourOfKind(histogram, cards):
    """
    Finds Four of a kind (four histogram with same value)

    :histogram: dictionary
    :returns: boolean

    """
    for i in histogram:
        if histogram[i] == 3:
            return find(cards, i)
    return False


def straight(cards):
    """
    Five cards in order
    :returns: TODO

    """
    pack = []
    for index,card in enumerate(cards):
        if len(pack) == 4:
            pack.append(card)
            return pack            
        control = cardsOrder.index(card[0]) - cardsOrder.index(cards[index+1][0])
        if control == 1:        
            pack.append(card)
        elif control == 0:
            continue
        else:
            return False



def sortCards(cards):
    """
    Sort cards from highest based on values

    :cards: TODO
    :returns: TODO

    """
    return sorted(cards, key = lambda a: (cardsOrder.index(a[0]), a[1]), reverse=True)

def flush(cards):
    """
    Five cards of the same suit
    :returns: TODO

    """
    #it will lookup the biggest flush in cards
    suits = ["Spades", "Clubs", "Diamonds", "Hearts"]

    for suit in suits:
        pack = []
        for card in cards:
            if card[1] == suit:
                pack.append(card)
        if len(pack) >= 5:
            return pack
    return False
    """
    for i in suits:
        pack=[]
        for j in cards:
            if j[1] is i:
                pack.append(j)
            if len(pack) >= 5:
                return pack
    return False
    """

def fullHouse(histogram, cards):
    """
    A pair and 3 of a kind
    :returns: TODO

    """
    pack = []
    for i in histogram:
        if histogram[i] == 1 or histogram[i] == 2:
            pack += find(cards, i)
    return pack if len(pack) == 5 else False


def straightFlush(cards):
    """
    Straight and flush
    :returns: TODO

    """
    # not functioning properly:  <25-07-19, dave> #
    flushCards = flush(cards)
    straightCards = straight(cards)
    if straightCards == flushCards:
        return straightCards
    return False

def royalFlush(cards):
    """
    The highest cards on hand. 
    all of the same color: 10,jack,queen, king, ace 
    :returns: TODO

    """
    royal = [10, "Jack", "Queen", "King", "Ace"]
    flushCards = flush(cards)
    if flushCards:    
        for i in flushCards:
            if i[0] not in royal:
                return False
        return flushCards
    return False



def findHandValue(cards):
    """
    Goes through the list of possible hands to find best one from top to the bottom

    :player: TODO
    :returns: float/int hand value of the player

    """
    histogram = createHistogram(cards)
    options = [royalFlush(cards),
               straightFlush(cards),
               fourOfKind(histogram, cards),
               fullHouse(histogram, cards),
               flush(cards),
               threeOfKind(histogram, cards),
               twoPairs(histogram, cards),
               pair(histogram, cards),]
    
    for index,option in enumerate(options):
        if option:
            #royalflush has lowest index so we invert values 
            #bigger number means better hand 
            return (8 - index) + highCard(cards)
    return highCard(cards)

