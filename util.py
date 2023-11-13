


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
    def __init__(self, suits, faces, specials):
        """
        Normal cards: Encompasses every possible suit, face combo as
        specified by the suits and faces collection.

        Special cards: Unique cards. Use "specials" argument to pass in
        2-value tuples, the first value containing the "special" card,
        the second containing the number of this card per deck.
        """
        self.cards = {}
        self.deck_size = len(suits) * len(faces)
        for (i, j) in specials:
            


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
