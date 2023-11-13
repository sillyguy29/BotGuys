import random

class Card:
    """
    This data type represents the playing cards found in a standard
    52-card deck.
    """
    def __init__(self, suit, face):
        """
        suit is H, D, S, C, for Heart, Diamond, Spade, Club
        face is 2-10, J, Q, K, A, for the numbered and real face cards
        value refers to the numerical value as used in Blackjack
            Ace cards should have value set to 1
        """
        self.suit = suit
        self.face = face

    def __eq__(self, other):
        return self.suit == other.suit\
                and self.face == other.face\
    
    def __str__(self):
        return str(self.suit) + str(self.face)
    
class Deck:
    """
    Contains cards and their weights to make drawing easy. Due to
    difficulty, it does not actually keep track of a deck. Can
    be made more memory efficient by placing a reference to each
    card in each slot rather than a whole card
    """
    def __init__(self, suits, faces, count, specials):
        """
        Normal cards: Encompasses every possible suit, face combo as
        specified by the suits and faces collection. Count determines
        how many of each normal card appears in a standard deck.

        Special cards: Unique cards. Use "specials" argument to pass in
        2-value tuples, the first value containing the "special" card
        (must be an actual card object), the second containing the
        number of this card per deck.
        """
        self.cards = []
        self.single_deck_size = len(suits) * len(faces) * count
        for i in suits:
            for j in faces:
                for k in range(count):
                    self.cards.append(Card(i, j))
        for (i, j) in specials:
            self.single_deck_size += j
            for k in range(j):
                self.cards.append(i)

    def draw(self, count):
        """
        Draws the number of cards specified by count, and returns them
        as a list.
        """
        ret_cards = []
        for i in range(count):
            ret_cards.append(self.cards[random.randint(0, self.single_deck_size - 1)])
        return ret_cards
    

STANDARD_52_DECK = Deck(('D', 'H', 'S', 'C'), 
                        ('A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'),
                        1, ())
        
def cards_to_str_52_standard(cards):
    ret = ""
    for card in cards:
        ret += card.face
        if card.suit == "D":
            ret += ":diamonds: "
        elif card.suit == "H":
            ret += ":hearts: "
        elif card.suit == "S":
            ret += ":spades: "
        elif card.suit == "C":
            ret += ":clubs: "
    return ret

def generate_deck():
    deck = []
    for suit in ('H', 'D', 'S', 'C'):
        deck.append(Card(suit, 'A'))
        for value in range(2,11):
            deck.append(Card(suit, str(value)))
        for face in ('J', 'Q', 'K'):
            deck.append(Card(suit, face))       
    return deck
 
            
def generate_deck_UNO():
    deck = []
    for color in ('Red', 'Yellow', 'Green', 'Blue'):
        deck.append(Card(color, '0'))
        for value in range(1,10):
            deck.append(Card(color, str(value)))
            deck.append(Card(color, str(value)))
        for value in range(0,2):
            deck.append(Card(color, "+2"))
            deck.append(Card(color, "Reverse"))
            deck.append(Card(color, "Skip"))
    for value in range(0,4):
        deck.append(Card("Wild", ""))
        deck.append(Card("Wild", "+4"))
    return deck
