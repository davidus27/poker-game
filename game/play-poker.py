"""
File: poker.py
Author: dave
Github: https://github.com/davidus27
Description: Game is the main Object implementing all the necessary tools for playing. Game is created in function main()
                        RUNS THE WHOLE PROGRAM!
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
        :arg1: TODO
        :returns: TODO

        """
        deposit = self.players[0].deposit #reference
        for player in self.players[:1]:
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
            for index,player in enumerate(self.players[:]):
                record = player.options()
                index = (index + 1) % len(self.players)
                               
                self.players[index].bet = record[0]
                if record[1] == -1:
                    self.players.remove(player)
                else:
                    self.dealer.playerControl.pot += record[1]
         
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
        #nedobre
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

    def showdown(self):
        """
        Ending of the round
        :returns: TODO

        """
        print("Community cards:")
        ui.cards(self.dealer.cardControl.tableCards)
        for player in self.players:
            print(player.name, "")
            ui.cards(player.hand)
        winners = self.dealer.chooseWinner(self.players)
        x = [winner.name for winner in winners]
        ui.roundWinners(x)
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
            
        if self.players[0].bet != -1:
            #Turn
            self.startPhase("Turn")

        if self.players[0].bet != -1:
            #River
            self.startPhase("River")
        
        else:
            #All-in case
            self.dealer.cardOnTable("All")


def main():
    """ 
    Work to create game
    """
    game = Game()
    print("Let's play Texas Hold'em!\n")
    allPlayers = game.createPlayers()
    while True:
        #The simple game functioning:
        #Players bets on preflop (before the release of firt three cards)
        #First three cards are released
        #Another beting
        #Turn-fourth card release
        #Another bets
        #River-final card
        #Last beting
        #Showdown-cards are showed (if any players are left)
        
        #  deleting players that loose:  <29-07-19, dave> # 
        game.players = list(allPlayers)
        
        game.dealer.gameOn()
        game.dealer.giveCards()
        game.eachRound()
        #Showdown
        print("\n\t\tShowdown\n")
        game.showdown()
        game.dealer.endGame()
        if len(game.dealer.playerControl.players) == 1:
            print("Final winner is:", game.dealer.playerControl.players[0].name)
            print("Money: ", game.dealer.playerControl.players[0].money)
            break

        input("Press Enter to continue.") 
        
        game.rounds += 1
        

if __name__ == "__main__":
    main()

