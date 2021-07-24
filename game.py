import random

# Tractor card ranks
ranks = {
    "THREE": 1,
    "FOUR": 2,
    "FIVE": 3,
    "SIX": 4,
    "SEVEN": 5,
    "EIGHT": 6,
    "NINE": 7,
    "JACK": 8,
    "QUEEN": 9,
    "KING": 10,
    "ACE": 11,
    "TWO": 12,
    "TEN": 13
}
JOKER = 14

suits = {
    "HEARTS": 1,
    "SPADES": 2,
    "DIAMONDS": 3,
    "CLUBS": 4
}

jokers = {
    "BLACK": 1,
    "RED": 2
}

class Card:
    rank = 0
    suit = 0

    def __init__(self, rank, suit):
        if rank == "JOKER":
            self.rank = JOKER
            self.suit = jokers[suit]
        else:
            self.rank = ranks[rank]
            self.suit = suits[suit]

    def fileName(self):
        if self.rank == JOKER:
            rank = "joker"
            suit = "black" if self.suit == 1 else "red"
        else:
            rank = list(ranks.keys())[list(ranks.values()).index(self.rank)].lower()
            suit = list(suits.keys())[list(suits.values()).index(self.suit)].lower()
        
        numbers = ["two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
        for i, num in enumerate(numbers):
            if num == rank:
                rank = i + 2
                break

        return suit + "_" + str(rank) + ".svg"

    def rand(self):
        self.rank = random.randint(1, 13)
        self.suit = random.randint(1, 4)

    def getRank(self):
        return "JOKER" if self.rank == JOKER else list(ranks.keys())[list(ranks.values()).index(self.rank)]
    
    def getSuit(self):
        return list(jokers.keys())[list(jokers.values()).index(self.suit)] if self.rank == JOKER else list(suits.keys())[list(suits.values()).index(self.suit)]
    

class Deck:
    cards = []

    def __init__(self, decks):
        for _ in range(decks):
            for rank in ranks:
                for suit in suits:
                    self.cards.append(Card(rank, suit))
            self.cards.append(Card("JOKER", "BLACK"))
            self.cards.append(Card("JOKER", "RED"))
    
    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()