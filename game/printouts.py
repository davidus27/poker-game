"""
File: printouts.py
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
    return input("Choose difficulty (easy/normal/hard) [easy]: ") 


def info(name, money, rounds):
    """
    Printout basic info about player

    :returns: 

    """
    print("Name:{}".format(name))
    print("Balance:{}".format(money))
    print("Round:{}".format(rounds))



def numQuest():
    """
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

