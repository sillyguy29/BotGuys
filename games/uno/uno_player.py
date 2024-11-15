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

    def get_card_category(self,card):
        """
        finds the category string used in variable values for a given card
        """
        #card type and name to general name categories used in option values dictionary
        #I am sorry and am on 5 hours of sleep, it is taking me 30 seconds to do 17-7.
        opt_val = {
            ("Wild","Draw Four"): "plus_fours",
        }
        for color in ('Red', 'Yellow', 'Green', 'Blue'):
            opt_val[(color, "Draw Two")]= "plus_twos"
            opt_val[(color, "Skip")]= "effect_cards"
            opt_val[(color, "Reverse")]= "effect_cards"
        if card not in opt_val:
            return None
        return opt_val[(card.name,card.value)]

    def is_normal_card(self,card):
        """
        Simple check to see if card falls in the effect, plus two, or plus four card categories
        """
        return self.get_card_category(card) is None

    def get_playable_cards(self, top_card, variables):
        """
        Used by the button menu to determine which cards can be
        enabled.
        """
        playable_cards = [
            card
            for card in
            self.hand
            if
            card.name == top_card.name or
            card.value == top_card.value or
            (
                card.name == "Wild" and
                (
                    not variables.get_value_of(
                    "Cannot play wild cards with matching color"
                    ) or
                    top_card.name not in [c.name for c in self.hand]
                )
            )
        ]
        return playable_cards

    def is_stackable_card(self, card, variables, queue_card):
        """
        returns a boolean for if a given card would be stackable on the last card in the queue of
        cards to have their effects applied
        """
        #I would indent better here but the linter settings disallow lines that are longer than 100
        #characters
        return (f"can_stack_{self.get_card_category(card)}_on_{self.get_card_category(queue_card)}"
            in variables.get_value_of("Stacking allowances")
            ) and not self.is_normal_card(card)

    def get_stackable_playable_cards(self, top_card, variables, queued_cards):
        """
        returns a list of the playable and stackable cards, used to replace playable cards deck
        if the player is the target of the card queue
        """
        try:
            queue_card = queued_cards[-1] #last queued card
        except IndexError:
            print("This should never happen, someone's not checking queued_cards before this")

        stackable_cards = [
            card
            for card in
            self.get_playable_cards(top_card,variables)
            if self.is_stackable_card(card, variables, queue_card)
        ]
        return stackable_cards

    def has_stackable_playable_cards(self, top_card, variables, queued_cards):
        """
        returns a boolean for if the player has any playable cards that could be stacked on
        the top card based on the current preferences.
        """
        return len(self.get_stackable_playable_cards(top_card, variables, queued_cards)) > 0

    def has_playable_cards(self, top_card, variables):
        """
        returns a boolean value for if the player has cards that could, without accounting for
        effects applied, be played on the top card  based on the current preferences.
        """
        return len(self.get_playable_cards(top_card,variables)) > 0

    def should_be_skipped(self, top_card, variables, queued_cards):
        """
        returns a boolean value for if the player has cards that can be played based upon
        whether or not there are stacked effects waiting and what cards they have available
        to play.
        """
        queued_card_effects = [self.get_card_category for card in queued_cards]
        return (len(queued_cards) > 0
            and self.has_stackable_playable_cards(top_card, variables, queued_cards)
            and any(x in queued_card_effects for x in ["plus_twos", "plus_fours"]))
