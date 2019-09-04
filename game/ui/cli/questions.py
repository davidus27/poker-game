"""
File: questions.py
Author: dave
Github: https://github.com/davidus27
Description: The CLI of the game on terminal. Collects input from the player and sends it to the main game logic (poker.py)
"""
   
def nameQuest():
    """
    Asks about name of the player
    :returns: TODO

    """
    x = input("What is your name (Player0): ")  
    return x if x != "" else "Player0"

def diffQuest():
    """
    Asks about difficulty of game
    :returns: difficulty
    """
    x = input("Choose difficulty (easy/normal/hard) [easy]: ") 
    return x if x != "" else "easy"


def allinOrFold():
    """
    The warning that player can only go allin or fold
    :returns: TODO

    """
    while True:
        print("Choose your option:")
        print("\t1) All-in")
        print("\t2) Fold")
        print("\t0) Exit")
        print("[0-2]")
        try:
            return int(input(">")) % 3
        except:
            print("You need to put number.")
    

def info(name, money):
    """
    Printout basic info about player

    :returns: 

    """
    print("Name:{}".format(name))
    print("Balance:{}".format(money))

def raising(minimum, maximum):
    """
    Decorator
    Asks the player how much will he raise the pot
    :returns: TODO

    """
    #return raised if raised == type(int) and raised >= minimal and raised <= maximum else False
    return int(input("How much do you want to raise [{0}-{1}]: ".format(maximum, minimum)))

def numQuest():
    """
    Decorator
    Asks about number of players
    :returns: numPlayers 

    """
    while True:
        try:
            x = input("How many players do you want to play with? (1-9)[2]: ")
        except ValueError:
            print("You need to input a number between 1 and 10")
        finally:
            if x == "":
                numPlayers = 2
                return numPlayers
            elif int(x) > 10 or int(x) < 1:
                print("Out of the range, Try again.")
             
            else:
                numPlayers = int(x)
                return numPlayers
 
 
def optionsInput():
        """
        Decorator
        Prints out the options of the player

        :returns: users option as a number

        """
        while True:
            print("Choose your option:")
            print("\t1) Check")
            print("\t2) Call")
            print("\t3) Raise")
            print("\t4) Fold")
            print("\t5) All-in")
            print("\t0) Exit")
            print("[0-5]")
            try:
                return int(input(">")) % 6
            except:
                print("You need to put number.")


