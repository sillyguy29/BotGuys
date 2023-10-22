
class Card:
    """
    This data type represents the playing cards found in a standard
    52-card deck.
    """
    def __init__(self, suit, face, value):
        """
        suit is H, D, S, C, for Heart, Diamond, Spade, Club
        face is 2-10, J, Q, K, A, for the numbered and real face cards
        value refers to the numerical value as used in Blackjack
            Ace cards should have value set to 1
        """
        self.suit = suit
        self.face = face
        self.value = value

    def __eq__(self, other):
        return self.suit == other.suit\
                and self.face == other.face\
                and self.value == other.value


def generate_deck():
    deck = []
    for suit in ('H', 'D', 'S', 'C'):
        deck.append(suit, 'A', 1)
        for value in range(2,11):
            deck.append(Card(suit, str(value), value))
        for face in ('J', 'Q', 'K'):
            deck.append(suit, face, 10)

def bj_add(cards):
    """
    cards is a list of Card objects
    returns an integer corresponding to the value of the hand in
    a game of blackjack
    """
    total = 0
    ace_count = 0
    for card in cards:
        if card.value != 1:
            total += card.value
        else:
            ace_count += 1
    total += 11 * ace_count
    for ace in range(ace_count):
        if total > 21:
            total -= 10
    return total
            