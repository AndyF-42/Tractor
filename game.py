import random
from typing import Tuple

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


class Card:
    def __init__(self, rank: str, suit: str):
        self.rank = rank # e.g., JACK or JOKER
        self.suit = suit # e.g., HEARTS or BLACK
        
        if rank == "FIVE":
            self.points = 5
        elif rank == "KING" or rank == "TEN":
            self.points = 10
        else:
            self.points = 0

    # return the image file name for this card
    def file_name(self) -> str:
        rank = self.rank.lower()
        suit = self.suit.lower()
        
        numbers = ["two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
        if rank in numbers:
            rank = numbers.index(rank) + 2

        return suit + "_" + str(rank) + ".svg"

    # return rank as number from 1-14
    def rank_num(self) -> int:
        return ranks[self.rank]
    
    # return suit as number (changes for dominants)
    def suit_num(self) -> int:
        return suits[self.suit]

    # return if card is dominant card
    def is_dominant(self) -> bool:
        return True if self.rank_num() >= 12 or self.suit_num() == max(list(suits.values())) else False

class Deck:
    def __init__(self, decks: int):
        self.cards = []
        for _ in range(decks):
            for rank in ranks:
                if rank != "JOKER":
                    for suit in suits:
                        if suit != "BLACK" and suit != "RED":
                            self.cards.append(Card(rank, suit))
            self.cards.append(Card("JOKER", "BLACK"))
            self.cards.append(Card("JOKER", "RED"))
    
    # shuffle deck in place
    def shuffle(self) -> None:
        random.shuffle(self.cards)

    # draw card from deck and return it
    def draw(self) -> Card:
        return self.cards.pop()
    
    def isempty(self) -> bool:
        return not self.cards

    def print(self) -> None:
        for card in self.cards:
            print(card.file_name())


# shift suit order to set the dominant suit
def set_dominant(dom_suit: str) -> None:
    suits[dom_suit] += 4
    # keep suit order alternating colors
    if dom_suit == "SPADES":
        suits["CLUBS"] -= 2
    elif dom_suit == "DIAMONDS":
        suits["SPADES"] -= 2

# return the cards in sorted order
def tractor_sorted(cards: list[Card]) -> list[Card]:
    special = [card for card in cards if card.rank_num() >= 12]
    cards = [card for card in cards if card.rank_num() < 12]
    cards.sort(key=lambda x: (x.suit_num(), x.rank_num()))
    special.sort(key=lambda x: (x.rank_num(), x.suit_num()))
    cards.extend(special)
    return cards


# NOTE: lots of 4-player-only functionality here

# return the type of play the cards are
# -1 = bad play, 1 = single, 2 = pair, 3 = tractor
def _type_of(cards: list[Card]) -> int:
    cards = tractor_sorted(cards)
    card_ranks = [ranks[card.rank] for card in cards]
    card_suits = [suits[card.suit] for card in cards]

    if card_suits.count(card_suits[0]) == len(card_suits): # all suits match
        if card_ranks.count(card_ranks[0]) == len(card_ranks): # all ranks match
            return len(cards)
        if (len(cards) == 4 and card_ranks[0] == card_ranks[1] and card_ranks[2] == card_ranks[3] and
            card_ranks[2] == card_ranks[1] + 1 and all([r < 12 for r in card_ranks])): # non-dom tractor
            return 3
    
    if (len(cards) == 4 and card_ranks[0] == card_ranks[1] and card_ranks[2] == card_ranks[3] and
        card_suits[0] == card_suits[1] and card_suits[2] == card_suits[3]): # checking dom tractors
        if (((card_ranks[0] == 11 and card_ranks[2] == 12) or (card_ranks[0] == 12 and card_ranks[2] == 13)) and
            card_suits[0] == max(list(suits.values())) and card_suits[2] != max(list(suits.values()))): # straddling dom tractor
            return 3 
        if ((card_ranks[0] == card_ranks[2] and (card_ranks[0] == 12 or card_ranks[0] == 13)) and
            card_suits[0] != max(list(suits.values())) and card_suits[2] == max(list(suits.values()))): # same rank dom tractor
            return 3
        if (card_ranks[0] == 13 and card_ranks[2] == 14 and card_suits[0] == max(list(suits.values())) and card_suits[2] == 1): # straddle joker tractor
            return 3
        if (card_ranks[0] == card_ranks[2] == 14 and card_suits[0] == 1 and card_suits[2] == 2): # all joker tractor
            return 3
    
    return -1

# returns the number of cards matching the suit
def _num_matching(checking: list[Card], suit: str, is_dom: bool) -> int:
    if is_dom:
        return len([card for card in checking if card.is_dominant()])
    else:
        return len([card for card in checking if card.suit == suit and not card.is_dominant()])

# returns if the hand has a play of the given type 
def _has_type(type: int, suit: str, is_dom: bool, hand: list[Card]) -> bool:
    if is_dom:
        of_suit = [card for card in hand if card.is_dominant()]
    else:
        of_suit = [card for card in hand if card.suit == suit and not card.is_dominant()]

    if type == 1:
        return True if of_suit else False
        
    if type == 2 or type == 3:
        of_suit = tractor_sorted(of_suit)
        for i in range(len(of_suit) - 1):
            if of_suit[i].rank == of_suit[i+1].rank and of_suit[i].suit == of_suit[i+1].suit: # has a pair
                if type == 2:
                    return True
                elif _type_of(of_suit[i:i+4]) == 3: # has a tractor
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
def valid_play(starting: list[Card], selected: list[Card], hand: list[Card]) -> Tuple[bool, str]:
    if not starting: # no starting play, this is first play 
        return True if _type_of(selected) != -1 else False

    if len(selected) != len(starting) or len(selected) == 0:
        return False
    
    if _type_of(selected) == _type_of(starting) and ((selected[0].suit == starting[0].suit and not selected[0].is_dominant() and not starting[0].is_dominant()) or
                                                   (selected[0].is_dominant() and starting[0].is_dominant())):
        return True
    
    if _has_type(_type_of(starting), starting[0].suit, starting[0].is_dominant(), hand):
        return False
    
    if _type_of(selected) == 2 and _type_of(starting) == 3 and ((selected[0].suit == starting[0].suit and not selected[0].is_dominant() and not starting[0].is_dominant()) or
                                                              (selected[0].is_dominant() and starting[0].is_dominant())): # pair is fine for tractor
        return True
    if _has_type(2, starting[0].suit, starting[0].is_dominant(), hand): # need to play pair
        return False
    
    if _num_matching(selected, starting[0].suit, starting[0].is_dominant()) == min(len(starting), _num_matching(hand, starting[0].suit, starting[0].is_dominant())):
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
def is_better(best: list[Card], playing: list[Card]) -> bool:
    if not best:
        return True

    if _type_of(best) > _type_of(playing): # better type
        return False

    if best[0].is_dominant() and not playing[0].is_dominant(): # dom > nondom
        return False
    
    print(str(best[0].is_dominant()) + " " + str(playing[0].is_dominant()))
    if not best[0].is_dominant() and playing[0].is_dominant(): # dom  > nondom
        return True

    if not best[0].is_dominant() and best[0].suit != playing[0].suit: # both nondom but different, best is original suit and wins
        return False

    if not best[0].is_dominant(): # both nondom same suit, winner determined by rank
        return True if playing[0].rank_num() > best[0].rank_num() else False
    
    if best[0].rank != playing[0].rank: # both dom, different ranks, winner is the higher one
        return True if playing[0].rank_num() > best[0].rank_num() else False
    
    if playing[0].suit != best[0].suit: # both dom, same rank, different suits, playing is better if dom suit or red joker  
        return True if playing[0].suit_num() == max(list(suits.values())) or playing[0].suit_num() == 2 else False

    return False # both dom, same rank, same suit, precedence is first played
    

# TODO 
# ----------
# - tractors >4 cards