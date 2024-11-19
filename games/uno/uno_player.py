"""
The module containing the Uno player class, an uno player has hand, skipped and active_interation
properties
"""

from games.game import BasePlayer

class UnoPlayer(BasePlayer):
    """
    Represents an player of the uno game. Extended from the BasePlayer
    class to include a few extra attributes: a list that represents
    the player's hand, a boolean to flag when the player has been 
    skipped, and a method to determine which cards in the player's 
    hand are playable given the game state's top card. 
    
    active_interaction serves as a reference to the interaction of 
    pressing the "Show Hand" button. We need to track it so that we
    can delete the interaction message if the player presses "Draw"
    instead of a playing a card. Otherwise, the "Show Hand" menu
    will linger until it deletes itself. 
    """
    def __init__(self):
        super().__init__()
        self.hand = []
        self.skipped = False
        self.active_interaction = None