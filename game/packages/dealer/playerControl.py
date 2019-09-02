import dealer
from detector import sortCards,findHandValue

class PlayerControlFlow(Dealer):
    def __init__(self):
        super().__init__(self)
    
    def cleanPlayers(self):
        for index,player in enumerate(self.players[:]):
            if player.money == 0:
                self.players.remove(player)
    
    
    def addPlayer(self,player):
        self.players.append(player)
        return self


    def createPlayers(self,name,numPlayers=2,money=500.0, difficulty="easy"):
        self.addPlayer(player.Player(name,money))
        for i in range(1,numPlayers+1):
            if difficulty == "easy":
               self.addPlayer(player.EasyBot())
               self.players[i].name +=str(i)
        return self


#  change!!!:  <30-08-19, yourname> # 
    def listPlayingCards(self, player):
        """
        Lists the players working cards (Player's hand + kickers)

        :cards: TODO
        :returns: best possible hand with kickers

        """
        kickers = self.listCards(player)
        return (player.hand + kickers)[:5] 
    
    def calculateHandValues(self, players):
        """
        Creates a list of hand values of everybody playing

        :players: TODO
        :returns: TODO

        """
        for player in players:
            cards = sortCards(self.listCards(player))
            player.handValue = findHandValue(cards)
        return players

    def chooseWinner(self, players):
        """
        Decides who wins the prize by sorting players by their handValues

        :players: TODO
        :returns: winning player, or list of players if more then one

        """
        players = self.calculateHandValues(players)
        for player in players:
            print(player.name, player.handValue)
        players = sorted(players, key = lambda x: x.handValue, reverse = True)
        #players.sort(reverse = True) #get lambda to sort by hand value attribute 
        winners = [players[0]]
        for player in players[1:]:
            if player.handValue != winners[0].handValue:
                break
            else:
                winners.append(player)
        return winners

    def givePot(self,players):
        """
        Gives the pot to the winner(s)
        :returns: TODO

        """
        prize = self.pot/len(players)
        for i in players:
            i.money += prize
        self.pot = 0.0
 
