"""
File: poker.py
Author: dave
Github: https://github.com/davidus27
Description: Game is the main Object implementing all the necessary tools for playing. Game is created in function main()
                        RUNS THE WHOLE PROGRAM!
"""
import dealer
import cli
import detector
import os
class Game(object):
    """
    Creates players based on inputs on call.
    """
    def __init__(self):
        self.rounds = 1
        self.players = []
        self.dealer = dealer.Dealer()



    def createPlayers(self):
        self.dealer.createPlayers(name = cli.nameQuest(),
                                  numPlayers = cli.numQuest(),
                                  money = 500,
                                  difficulty = cli.diffQuest()
                                  )
        return self.dealer.players

    def giveCards(self):
        """
        gives cards.
        :returns: TODO

        """
        self.dealer.dealCard()
        self.dealer.dealCard()

    def question(self):
        """
        Questions every player which option will be choosen
        :returns: TODO

        """
        for i in self.players:
            i.options()
        return self
 
    def gameOn(self):
        """
        Clears all the cards, create cards and shuffles them
        :returns: TODO

        """
        self.dealer.buildDeck()
        self.dealer.shuffle()
        return self

    def controlDeposit(self):
        """
        checks if there are any differences
        :arg1: TODO
        :returns: TODO

        """
        deposit = self.players[0].deposit #reference
        for player in self.players:
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
                bet = player.options()
                x = (index + 1) % len(self.players)
                
                if bet[1] == -1:
                    self.players[x].bet = bet[0]
                    self.players.remove(player)
                else:
                    self.players[x].bet = bet[0]
                    self.dealer.pot += bet[1]
                print("Bet:{}\nDeposit:{}".format(player.bet,player.deposit))
                print("Pot:", self.dealer.pot)
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
        if type(self.players[0]) == dealer.player.Player:
            cli.info(self.dealer.players[0].name, self.dealer.players[0].money)
            print("Your cards:")
            cli.cards(self.dealer.players[0].hand)
            print()
            if table:
                print("Community cards:")
                cli.cards(table)
                print()
        return self

    def clearPlayersDebt(self):
        """
        Clears deposit and bet to all players
        :returns: TODO

        """
        for player in self.dealer.players:
            player.clearDebt()
        return self
    
    def endGame(self):
        """
        Clear players list, removes debt and recreates deck

        :returns: TODO

        """
        self.dealer.deck = []
        self.dealer.clearCards()
        self.dealer.cleanPlayers() 
        self.clearPlayersDebt()
        return self

    def showdown(self):
        """
        Ending of the round
        :returns: TODO

        """
        print("Community cards:")
        cli.cards(self.dealer.tableCards)
        for player in self.players:
            print(player.name, "")
            cli.cards(player.hand)
        winners = self.dealer.chooseWinner(self.players)
        x = [winner.name for winner in winners]
        cli.roundWinners(x)
        self.dealer.givePot(winners)
        return self

    def cardOnTable(self, phase):
        """
        Three cards on table while flop
        :returns: TODO

        """
        if phase == "Preflop":
            self.dealer.drawTable()
            self.dealer.drawTable()
            self.dealer.drawTable()
        elif phase == "River":
            pass
        elif phase == "All":
            self.dealer.drawTable()
            self.dealer.drawTable()
        else:
            self.dealer.drawTable()

    def oneRound(self, phase):
        """
        Creates flop part of easy game
        :returns: TODO

        """
        print("\n\t\t{}\n".format(phase))
        self.printSituation(self.dealer.tableCards)
        self.round()
        self.cardOnTable(phase)

def main():
    """ 
    Work to create game
    """
    game = Game()
    print("Let's play Texas Hold'em!\n")
    #game.askQuestions()
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
        
        game.gameOn()
        game.giveCards()
        print("\n\t\tRound", game.rounds)

        #Preflop
        phase = "Preflop"
        game.oneRound(phase)
        if game.players[0].bet != -1:

            #Flop
            phase = "Flop"
            game.oneRound(phase)
            
            #Turn
            phase = "Turn"
            game.oneRound(phase)

            #River
            phase = "River"
            game.oneRound(phase)
            
        else:
            phase = "All"
            game.cardOnTable(phase)
        #Showdown
        print("\n\t\tShowdown\n")
        game.showdown()
        game.endGame()
        if len(game.dealer.players) == 1:
            print("The winner is:", game.dealer.players[0].name)
            print("Money: ", game.dealer.players[0].money)
            break

        input("Press Enter to continue.") 
        
        game.rounds += 1
        
        #print(game.dealer.chooseWinner())



if __name__ == "__main__":
    main()

