"""
The module containing the Uno game data, i.e. the preferences, deck, turn order, whether the game
is running in reverse order, the currently stacked/queued cards, top_card, and used up cards are
stored and initialized here.
"""

from utils.variable_management.variable import IntegerVariable
from utils.variable_management.variable import OptionVariable
from utils.variable_management.variable import BooleanVariable
from utils.variable_management.variable import OptionRepresentation
from utils.variable_management.variable_storage import VariableStorage
from games.game import BaseGame
from games.uno.uno_card import UnoCard

class UnoGame(BaseGame):
    """
    Uno game model class to represent the game state of Uno. It is
    extended from BaseGame to include extra properties:
        1. deck: List of Card objects that represents the deck of 
           Uno cards.
        2. discard: List of Card objects that represents the discard 
           pile, required to be tracked to replenish the deck when 
           it's empty.
        3. turn_order: List of whatever type 'discord.interaction.user'
           is supposed to be. We use this list to maintain turn order.
        4. turn_index: Integer iterator over turn_order to know who
           the current turn belongs to.
        5. reversed: Boolean to flag when the turn_order should be
           reversed. 
        6. top_card: A Card object that represents the Uno card at 
           the middle of the table that the players need to match
           color or value.
    """
    def __init__(self, user_id):
        # game state 1 -> accepting players but not playing yet
        super().__init__(game_type=3, player_data={}, game_state=1, user_id=user_id)

        self.deck = []
        self.discard = []
        self.turn_order = []
        self.turn_index = 0
        self.reversed = False
        self.top_card = UnoCard("None", "")
        self.queued_cards = []
        #defines the variables for use and display
        preferences = [
            IntegerVariable("Drawn card show time", 5, range_min=0, range_max=20),
            IntegerVariable("Announcement lifetime", 0, range_min=0, range_max=20),
            OptionVariable(
                name="Stacking allowances",
                default_value=[
                    "can_stack_effect_cards_on_effect_cards",
                    "can_stack_plus_twos_on_effect_cards",
                    "can_stack_plus_fours_on_effect_cards",
                    "can_stack_effect_cards_on_plus_twos_cards",
                    "can_stack_plus_twos_on_plus_twos_cards",
                    "can_stack_plus_fours_on_plus_twos_cards",
                    "can_stack_effect_cards_on_plus_fours_cards",
                    "can_stack_plus_twos_on_plus_fours_cards",
                    "can_stack_plus_fours_on_plus_fours_cards"
                ],
                options=[
                    OptionRepresentation(
                        "Can stack effect cards on other effect cards",
                        "can_stack_effect_cards_on_effect_cards"
                    ),
                    OptionRepresentation(
                        "Can stack plus twos on effect cards",
                        "can_stack_plus_twos_on_effect_cards"
                    ),
                    OptionRepresentation(
                        "Can stack plus fours on effect cards",
                        "can_stack_plus_fours_on_effect_cards"
                    ),
                    OptionRepresentation(
                        "Can stack effect cards on plus twos",
                        "can_stack_effect_cards_on_plus_twos"
                    ),
                    OptionRepresentation(
                        "Can stack plus twos on other plus twos",
                        "can_stack_plus_twos_on_effect_cards"
                    ),
                    OptionRepresentation(
                        "Can stack plus fours on plus twos",
                        "can_stack_plus_fours_on_plus_twos"
                    ),
                    OptionRepresentation(
                        "Can stack effect cards on plus fours",
                        "can_stack_effect_cards_on_plus_fours"
                    ),
                    OptionRepresentation(
                        "Can stack plus twos on other plus fours",
                        "can_stack_plus_twos_on_effect_fours"
                    ),
                    OptionRepresentation(
                        "Can stack plus fours on other plus fours",
                        "can_stack_plus_fours_on_plus_fours"
                    ),
                ],
                min_selected=0,
                max_selected=9
            ),
            BooleanVariable("Reverse card repeats players turn",False),
            BooleanVariable("Cannot play wild cards with matching color",False)
        ]
        self.preferences_variables = VariableStorage(preferences)
        """
        self.drawn_card_show_time = 5
        self.make_deck_time = 0
        self.can_stack_effect_cards_on_effect_cards = True
        self.can_stack_plus_fours_on_effect_cards = True
        self.can_stack_effect_cards_on_plus_fours = True
        self.can_stack_plus_fours_on_plus_fours = True
        self.reverse_card_repeats_players_turn = False
        self.can_callout_uno = False
        self.only_play_plus_fours_without_matching_color = False
        """
