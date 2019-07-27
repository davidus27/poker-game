#!/usr/bin/python
# vim: set fileencoding=utf-8 :

"""
File: dealer.py
Author: dave
Github: https://github.com/davidus27
Description: We need to create a "Dealer" for a game so we can 
    easily manage a pot (money on a table) cards on a table, cards on hands,shuffling and who wins.
"""


import player
import detector
import random


class Dealer(object):
    def __init__(self,numPlayers):
        self.deck = []
        self.players = []
        self.tableCards = []
        self.numPlayers = numPlayers
        self.pot = 0

