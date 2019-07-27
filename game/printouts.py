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
