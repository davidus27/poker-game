suits = {"Spades" : "♠" , "Clubs" : "♣" , "Diamonds" : "♦" , "Hearts": "♥"}

def firstLine(cards):
    """
    For every card creates first line of the ascii card
    :returns: TODO

    """
    for i in cards:
        #print("    ", end = "")
        print("     _______ ", end = "")
    print()

def secondLine(cards):
    """
    Creates for each card second line which shows the value in left corner
    :cards: TODO
    :returns: TODO

    """
    for i in cards:
        print("    ", end= "")
        if type(i[0]) == type(""):
            print("|{0}      |".format(i[0][0]), end="")
        elif i[0] == 10:
            print("|{0}     |".format(i[0]), end="")
        else:
            print("|{0}      |".format(i[0]), end="")
    print()

def middleLine(cards):
    """
    Middle lines contain suit in the middle of card ascii
    :arg1: TODO
    :returns: TODO
    """
    for i in cards:
        print("    ", end="")
        print("|   {0}   |".format(suits[i[1]]), end="")
    print()


def lastLine(cards):
    """
    Last line creates ending seperation and number in right corner
    """
    for i in cards:
        print("    ", end = "")
        if i[0] == 10:
            print("|_____{0}|".format(i[0]), end="")
        elif type(i[0]) == type(""):
           print("|______{0}|".format(i[0][0]), end="")
        else:
           print("|______{0}|".format(i[0]), end="")
    print()

def cards(cards):
    """
    Prints out cards of the player in the CLI-like way
    :arg1: TODO
    :returns: TODO

    """
    firstLine(cards)
    secondLine(cards)
    middleLine(cards)
    middleLine(cards)
    middleLine(cards)
    lastLine(cards)


