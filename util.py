import random
import discord

class Card:
    """
    This data type represents the playing cards found in a standard
    52-card deck.
    """
    def __init__(self, name, value):
        """
        name (suit) is H, D, S, C, for Heart, Diamond, Spade, Club
        value (face) is 2-10, J, Q, K, A, for the numbered and real face cards
        value refers to the numerical value as used in Blackjack
            Ace cards should have value set to 1
        """
        self.name = name
        self.value = value

    def __eq__(self, other):
        return self.name == other.name\
                and self.value == other.value\
    
    def __str__(self):
        return str(self.name) + str(self.value)
    
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
        ret += card.value
        if card.name == "D":
            ret += ":diamonds:, "
        elif card.name == "H":
            ret += ":hearts:, "
        elif card.name == "S":
            ret += ":spades:, "
        elif card.name == "C":
            ret += ":clubs:, "
    return ret.rstrip(", ")

def generate_deck():
    deck = []
    for suit in ('H', 'D', 'S', 'C'):
        deck.append(Card(suit, 'A'))
        for value in range(2,11):
            deck.append(Card(suit, str(value)))
        for face in ('J', 'Q', 'K'):
            deck.append(Card(suit, face))       
    return deck


async def double_check(interaction, message_content="", timeout=30):
    """
    Utility function that asks users if they are sure about what they
    are doing through a button prompt. Returns a 2-value tuple, the
    first value containing a boolean storing the user response where
    True == yes and False == no. The second value an interaction that
    the program can respond to accordingly.

    Params:
    message_content: the content to place above the "are you sure"
    segment of the message. Defaults to nothing.
    timeout: the time before the menu defaults to no, in seconds.
    Defaults to 30.
    """
    view = AreYouSureButtons()
    await interaction.response.send_message(content=(f"{message_content}\nAre you sure?"
                                            f" (will auto-no in {str(timeout)} seconds.)"),
                                            view=view, delete_after=timeout, ephemeral=True)
    # wait for the view to finish
    await view.wait()
    # if we didn't get any button interaction, default to no and
    # send back the old interaction so we can respond to that instead
    if view.button_interaction is None:
        return (False, interaction)
    # else, return the result of the interaction (and delete the msg)
    await interaction.delete_original_response()
    return (view.result, view.button_interaction)


class AreYouSureButtons(discord.ui.View):
    """
    Helper class designed to facilitate a double check from the user upon trying to perform
    certain actions
    """
    def __init__(self):
        super().__init__()
        self.result = False
        self.button_interaction = None

    @discord.ui.button(label = "Yes", style = discord.ButtonStyle.green)
    async def yes_pressed(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.result = True
        self.button_interaction = interaction
        self.stop()

    @discord.ui.button(label = "No", style = discord.ButtonStyle.red)
    async def no_pressed(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.button_interaction = interaction
        self.stop()
