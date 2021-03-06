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
    "TEN": 13,
    "JOKER": 14
}

suits = {
    "BLACK": 1, # for jokers
    "RED": 2,

    "HEARTS": 4,
    "SPADES": 5,
    "DIAMONDS": 6,
    "CLUBS": 7
}

# jokers = {
#     "BLACK": 1,
#     "RED": 2
# }



class Card:
    rank = ""
    suit = ""
    points = 0

    def __init__(self, rank, suit):
        if rank in ranks and suit in suits:
            self.rank = rank
            self.suit = suit
        
        if rank == "FIVE":
            self.points = 5
        
        if rank == "KING" or rank == "TEN":
            self.points = 10
            
        # if rank == "JOKER":
        #     self.rank = JOKER
        #     self.suit = jokers[suit]
        # else:
        #     self.rank = ranks[rank]
        #     self.suit = suits[suit]

    # return the image file name for this card
    def file_name(self):
        rank = self.rank.lower()
        suit = self.suit.lower()
        
        numbers = ["two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
        if rank in numbers:
            rank = numbers.index(rank) + 2

        return suit + "_" + str(rank) + ".svg"

    # choose a random rank and suit
    def rand(self):
        self.rank = random.choice(list(ranks.keys()))
        self.suit = random.choice(list(suits.keys()))

    # return rank as text, e.g., JACK or JOKER
    def get_rank(self):
        return self.rank
        # return "JOKER" if self.rank == JOKER else list(ranks.keys())[list(ranks.values()).index(self.rank)]
    
    # return suit as text, e.g., HEARTS or BLACK
    def get_suit(self):
        return self.suit
        # return list(jokers.keys())[list(jokers.values()).index(self.suit)] if self.rank == JOKER else list(suits.keys())[list(suits.values()).index(self.suit)]
    
    # return points
    def get_points(self):
        return self.points

    # return rank as number from 1-14
    def rank_num(self):
        return ranks[self.rank]
    
    # return suit as number from 1-4 (changes for dominants)
    def suit_num(self):
        return suits[self.suit]


    def update_suit(self, dom_suit):
        # swap suits to make it Red Black Red Black
        if self.suit == suits[dom_suit]:
            self.suit += 4
        elif (self.suit == suits["CLUBS"] and dom_suit == "SPADES") or (self.suit == suits["SPADES"] and dom_suit == "DIAMONDS"):
            self.suit -= 2
    
    def is_dominant(self):
        return True if self.rank_num() >= 12 or self.suit == max(list(suits.values())) else False
    


class Deck:
    cards = []

    def __init__(self, decks):
        for _ in range(decks):
            for rank in ranks:
                if rank != "JOKER":
                    for suit in suits:
                        if suit != "BLACK" and suit != "RED":
                            self.cards.append(Card(rank, suit))
            self.cards.append(Card("JOKER", "BLACK"))
            self.cards.append(Card("JOKER", "RED"))
    
    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()
    
    def isempty(self):
        return not self.cards

    def sort(self):
        special = [card for card in self.cards if card.rank_num() >= 12]
        self.cards[:] = [card for card in self.cards if card.rank_num() < 12]
        self.cards.sort(key=lambda x: (x.suit_num(), x.rank_num()))
        special.sort(key=lambda x: (x.rank_num(), x.suit_num()))
        self.cards.extend(special)

    def print(self):
        for card in self.cards:
            print(card.file_name())


def set_dominant(dom_suit):
    suits[dom_suit] += 4
    if dom_suit == "SPADES":
        suits["CLUBS"] -= 2
    elif dom_suit == "DIAMONDS":
        suits["SPADES"] -= 2

def tractor_sorted(cards):
    special = [card for card in cards if card.rank_num() >= 12]
    cards[:] = [card for card in cards if card.rank_num() < 12]
    cards.sort(key=lambda x: (x.suit_num(), x.rank_num()))
    special.sort(key=lambda x: (x.rank_num(), x.suit_num()))
    cards.extend(special)
    return cards


# NOTE: lots of 4-player-only functionality here

# -1 = bad play, 1 = single, 2 = pair, 3 = tractor
def type_of(cards):
    cards = tractor_sorted(cards)
    ranks = [card.get_rank() for card in cards]
    suits = [card.get_suit() for card in cards]
    if suits.count(suits[0]) == len(suits): # all suits match
        if ranks.count(ranks[0]) == len(ranks): # all ranks match
            return len(cards)
        if len(cards) == 4 and ranks[0] == ranks[1] and ranks[2] == ranks[3] and ranks[2] == ranks[1] + 1: # tractor! technically doesn't work perfectly for high doms but whatever
            return 3
    return -1

def num_matching(checking, suit, is_dom):
    if is_dom:
        return len([card for card in checking if card.is_dominant()])
    else:
        return len([card for card in checking if card.get_suit() == suit and not card.is_dominant()])

def has_type(type, suit, is_dom, hand):
    if is_dom:
        of_suit = [card for card in hand if card.is_dominant()]
    else:
        of_suit = [card for card in hand if card.get_suit() == suit and not card.is_dominant()]

    if type == 1:
        return True if of_suit else False
        
    if type == 2 or type == 3:
        of_suit = tractor_sorted(of_suit)
        for i in range(len(of_suit) - 1):
            if of_suit[i].get_rank() == of_suit[i+1].get_rank() and of_suit[i].get_suit() == of_suit[i+1].get_suit(): # has a pair
                if type == 2:
                    return True
                elif (i+3 < len(of_suit) and of_suit[i+2].get_rank() == of_suit[i+3].get_rank() and
                                             of_suit[i+2].get_suit() == of_suit[i+3].get_suit() and
                                             of_suit[i+2].get_rank() == of_suit[i].get_rank() + 1): # has a tractor
                    return True
    
    return False

"""
VALID PLAY
----------
1. if first play -> True if not bad play else False
2. if lengths dont match or you selected nothing -> False
3. if same type and ((same suit and neither are dom) or (both dom)) -> True
4. if has same type of same suit (has type will account for if suit is dom or not) -> False
---TRACTOR SPECIAL---
5. if selected type is pair and starting type is tractor and ((same suit and neither are dom) or (both dom)) -> True
6. if has a pair of the right suit -> False
---------------------
7. if num matching suit/dom in selected is same as min of length of starting and matching in hand -> True
8. -> False
"""

def valid_play(starting, selected, hand):
    if not starting:
        return True if type_of(selected) != -1 else False

    if len(selected) != len(starting) or len(selected) == 0:
        return False
    
    if type_of(selected) == type_of(starting) and ((selected[0].get_suit() == starting[0].get_suit() and not selected[0].is_dominant() and not starting[0].is_dominant()) or
                                                   (selected[0].is_dominant() and starting[0].is_dominant())):
        return True
    
    if has_type(type_of(starting), starting[0].get_suit(), starting[0].is_dominant(), hand):
        return False
    
    if type_of(selected) == 2 and type_of(starting) == 3 and ((selected[0].get_suit() == starting[0].get_suit() and not selected[0].is_dominant() and not starting[0].is_dominant()) or
                                                              (selected[0].is_dominant() and starting[0].is_dominant())): # pair is fine for tractor
        return True
    if has_type(2, starting[0].get_suit(), starting[0].is_dominant(), hand): # need to play pair
        return False
    
    if num_matching(selected, starting[0].get_suit(), starting[0].is_dominant()) == min(len(starting), num_matching(hand, starting[0].get_suit(), starting[0].is_dominant())):
        return True

    return False
     

"""
IS BETTER
---------
1. better type
2. is "best" a dom and "playing" not? -> false
3. is "playing" a dom and "best" not? -> true
4. if "best" not dom and "best" suit != "playing" suit -> false  (both non-dominant, so best must be the original suit)
5. if "best" not dom: -> True if "playing" rank > "best" rank else False
6. if "best" rank != "playing" rank: -> True if "playing" rank > "best" rank else False
7. if "playing" suit != "best" suit: -> True if "playing" suit is max or "playing" suit is 2
8. -> false
"""

def is_better(best, playing):
    if not best:
        return True

    if type_of(best) > type_of(playing): # better type
        return False

    if best[0].is_dominant() and not playing[0].is_dominant(): # dom > nondom
        return False
    
    print(str(best[0].is_dominant()) + " " + str(playing[0].is_dominant()))
    if not best[0].is_dominant() and playing[0].is_dominant(): # dom  > nondom
        return True

    if not best[0].is_dominant() and best[0].get_suit() != playing[0].get_suit(): # both nondom but different, best is original suit and wins
        return False

    if not best[0].is_dominant(): # both nondom same suit, winner determined by rank
        return True if playing[0].rank_num() > best[0].rank_num() else False
    
    if best[0].get_rank() != playing[0].get_rank(): # both dom, different ranks, winner is the higher one
        return True if playing[0].rank_num() > best[0].rank_num() else False
    
    if playing[0].get_suit() != best[0].get_suit(): # both dom, same rank, different suits, playing is better if dom suit or red joker  
        return True if playing[0].suit_num() == max(list(suits.values())) or playing[0].suit_num() == 2 else False

    return False # both dom, same rank, same suit, precedence is first played
    

# Testing: 
# deck = Deck(2)
# deck.shuffle()
# deck.print()
# set_dominant("CLUBS")
# deck.sort()
# print("\n\n----------------------------\n\n")
# deck.print()