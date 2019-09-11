"""
File: poker.py
Author: dave
Github: https://github.com/davidus27
Description: Game is the main Object implementing all the necessary tools for playing. Game is created in function main()
"""
import ui
import dealer
from player import Player

class Game(object):
    """
    Creates players based on inputs on call.
    """
    def __init__(self):
        self.rounds = 1
        self.players = []
        self.dealer = dealer.Dealer()

    def createPlayers(self):
        name = ui.nameQuest()
        numPlayers = ui.numQuest()
        money = 500
        difficulty = ui.diffQuest()

        return self.dealer.playerControl.createPlayers(name,numPlayers, money, difficulty)

    def controlDeposit(self):
        """
        checks if there are any differences
        :returns: TODO

        """
        deposit = self.players[0].deposit #reference
        for player in self.players[1:]:
            if player.deposit == deposit:
                continue
            else:
                return False
        return True

    def round(self):
        """
        Goes through all players until every player gave same ammount to the pot
        :returns: TODO

        """
        while True:
            length = len(self.players[:])
            for index,player in enumerate(self.players[:]):
                record = player.options()
                i = index
                index = (index + 1) % length#len(self.players[:])
                
                self.players[index].bet = record[0]
                if record[1] == -1:
                    self.players.remove(player)
                    length -= 1
                else:
                    self.dealer.playerControl.pot += record[1]
                
                
                
                print("Size: ", length)#len(self.players)) 
                print("i: ", i) 
                print("Index:%d\nBet:%d\n" % (index, player.bet))
                print(record)
                print("Pot: ", self.dealer.playerControl.pot)
                
            if self.controlDeposit():
                break
            else:
                continue
        return self

    def printSituation(self, table=False):
        """
        Prints out whole situation in the game.
        :returns: TODO

        """
        if type(self.players[0]) == Player:
            ui.info(self.dealer.playerControl.players[0].name, self.dealer.playerControl.players[0].money)
            print("Your cards:")
            ui.cards(self.dealer.playerControl.players[0].hand)
            print()
            if table:
                print("Community cards:")
                ui.cards(table)
                print()
        return self

    def allCards(self):
        """
        Prints hands of all players
        """
        for player in self.players:
            print(player.name, "")
            ui.cards(player.hand)
        return self

    def showdown(self):
        """
        Ending of the round
        :returns: TODO

        """
        print("Community cards:")
        ui.cards(self.dealer.cardControl.tableCards)
        self.allCards()
        
        winners = self.dealer.chooseWinner(self.players)
        x = [winner.name for winner in winners]
        ui.roundWinners(x)
        for w in winners:
            ui.printValue(w.handValue)
        self.dealer.playerControl.givePot(winners)
        return self

    def startPhase(self, phase):
        """
        Goes through one phase part of easy game
        :returns: TODO

        """
        print("\n\t\t{}\n".format(phase))
        self.printSituation(self.dealer.cardControl.tableCards)
        self.round()
        self.dealer.cardOnTable(phase)
        
    
    def eachRound(self):
        """TODO: Docstring for function.

        :returns: TODO

        """
        #Preflop
        self.startPhase("Preflop")
        if self.players[0].bet != -1:
            #Flop
            self.startPhase("Flop")
        else:
            #allin on flop
            return self.dealer.cardOnTable("All-flop")
            
        if self.players[0].bet != -1:
            #Turn
            self.startPhase("Turn")
        else:
            #allin on turn
            return self.dealer.cardOnTable("All-turn")

