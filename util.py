
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


def generate_deck():
    deck = []
    for suit in ('H', 'D', 'S', 'C'):
        deck.append(Card(suit, 'A'))
        for value in range(2,11):
            deck.append(Card(suit, str(value)))
        for face in ('J', 'Q', 'K'):
            deck.append(Card(suit, face))       
    return deck
 
            
def generate_deck_Uno():
    deck = []
    for color in ('Red', 'Yellow', 'Green', 'Blue'):
        deck.append(Card(color, '0'))
        for value in range(1,10):
            deck.append(Card(color, str(value)))
            deck.append(Card(color, str(value)))
        for value in range(2):
            deck.append(Card(color, "+2"))
            deck.append(Card(color, "Reverse"))
            deck.append(Card(color, "Skip"))
    for value in range(4):
        deck.append(Card("Wild", ""))
        deck.append(Card("Wild", "+4"))
    return deck
