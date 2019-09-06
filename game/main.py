import poker

def main():
    """ 
    Work to create game
    """
    game = poker.Game()
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

