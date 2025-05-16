import math

def printValue(handValue):
    """
    Prints the value of the player's card

    :card: TODO
    :returns: TODO

    """
    options = { 0: highcard,
                1: pair,
                2: twoPairs,
                3: threeOfKind,
                4: straight,
                5: flush,
                6: fullHouse,
                7: fourOfKind,
                8: straightFlush,
                9: royalFlush,
            }
    for o in options:
        if math.floor(handValue) == o:
            options[o]()


def highcard():
    print("High Card")
def pair():
    print("Pair")
def twoPairs():
    print("Two pairs")
def threeOfKind():
    print("Three of kind")
def straight():
    print("Straight")
def flush():
    print("Flush")
def fullHouse():
    print("Full house")
def straightFlush():
    print("straight flush")
def fourOfKind():
    print("Four of a kind")
def royalFlush():
    print("Royal Flush")


