import dealer

class CardControlFlow(Dealer):
    def __init_(self):
        super().__init__(self)

    def buildDeck(self):
        """
        Creates list of cards.
        Individual cards are tuples with format: (number,color)
        """
        colors = ["Spades" , "Clubs", "Diamonds", "Hearts"]
        numbers = [2, 3, 4, 5, 6 ,7 ,8 , 9 ,10,"Jack", "Queen","King", "Ace"]
        for color in colors:
            for number in numbers:
                self.deck.append((number,color))
        return self

    def shuffle(self):
        for i in range(len(self.deck)-1 , 0, -1):
            rand = random.randint(0,i)
            self.deck[i], self.deck[rand]= self.deck[rand], self.deck[i]
        return self

    def drawCard(self):
        return self.deck.pop()


    def round(self):
        """
        Questions every player which option will be choosen
        :returns: TODO

        """
        for i in self.players:
            diff = i.options()
            if diff:
                self.players[self.players.index(i)+1].diff = diff 
        return self
            
    def dealCard(self):
        """
        Deals cards to everyone
        :returns: self

        """
        for i in self.players:
            i.hand.append(self.drawCard())
        return self 


    def drawTable(self):
        """
        Draw a card on table
        :returns: TODO

        """
        self.tableCards.append(self.drawCard())
        return self

    def listCards(self, player):
        """
        Creates the list of cards for specific player

        :player: object Player()
        :returns: list of cards on table and hand of specific player

        """
        return self.tableCards + player.hand

    def clearCards(self):
        """
        Clear all played cards
        :returns: TODO

        """
        self.tableCards = []
        for index,player in enumerate(self.players):
            self.players[index].hand = []
        return self
 
