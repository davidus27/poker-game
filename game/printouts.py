"""
File: printouts.py
Author: dave
Github: https://github.com/davidus27
Description: The CLI of the game on terminal. Collects input from the player and sends it to the main game logic (poker.py)
"""

class PrintOuts(object):
    """
    Manages game's behaviour on terminal
    """

    def __init__(self, name="Player0", numPlayers=2, difficulty="easy"):
        self.name = name
        self.money = 500.0
        self.numPlayers = numPlayers
        self.difficulty = difficulty


       
    def nameQuest(self):
        """
        Asks about name of the player
        :returns: TODO

        """
        x = input("What is your name (Player0): ")  
        self.name = x if x != "" else "Player0"
        return self

    def diffQuest(self):
        """
        Asks about difficulty of game
        :returns: difficulty
        """
        self.difficulty = input("Choose difficulty (easy/normal/hard) [easy]: ") 
        return self.difficulty
   
   
    def info(self, name, money, rounds ):
        """
        Printout basic info about player

        :returns: self

        """
        print("Name:{}".format(name))
        print("Balance:{}".format(money))
        print("Round:{}".format(rounds))
        return self



    def numQuest(self):
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
                    self.numPlayers = 2
                    return self.numPlayers
                elif int(x) > 10 or int(x) < 1:
                    print("Out of the range, Try again.")
                 
                else:
                    self.numPlayers = int(x)
                    return self.numPlayers

