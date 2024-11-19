"""Uno game module

Contains all the logic needed to run a game of Uno.
It features an closed game model, meaning not all users can interact
with the game at any time, and there is player management.
"""
import random
import discord
from games.game import GameManager
from games.uno.uno_card import UnoCard
from games.uno.uno_game import UnoGame
from games.uno.uno_player import UnoPlayer
import games.uno.uno_views as Views

#TODO separate view for users who can affect it maybe
#TODO implement dismissing preferences menu after game starts
#TODO disable preferences button after game start
#TODO show settings in join message
#TODO single instance of preferences_gui view may cause issues with dynamic preference adding.
#TODO setup rows for preferences menu to fix annoying ui element ordering
#TODO implement effect stacking
#TODO reimplement UNO from scratch to use new view system
#TODO   write play_card, and next_turn methods

class UnoManager(GameManager):
    '''
    Uno game model class that controls the flow of Uno by interacting
    and modifying its UnoGame property and updating its base GUI to
    receive input from the players.
    '''
    def __init__(self, factory, channel, user_id=None):
        gui_by_game_state = {
            0: None,
            1: Views.UnoButtonsBase(self),
            2: None,
            3: None,
            4: Views.UnoButtonsBaseGame(self),
        }
        super().__init__(
            game=UnoGame(user_id),
            channel=channel,
            factory=factory,
            gui_by_game_state=gui_by_game_state
        )
        self.prepare_preferences_menu()

    def prepare_preferences_menu(self):
        """
        Prepares the games preferences menu for 
        """
        self.preferences_menu.add_ui_element(Views.PreferencesQuitButton(self))
        self.preferences_menu.add_menu_items()

    async def add_player(self, interaction, init_player_data=UnoPlayer()):
        '''
        add_player: Called when a person presses the "Join" button.
        This method add the member to the game state's player_data as 
        well as adding their interaction.user to the turn_order.
        '''
        #init_player_data = UnoPlayer()
        await super().add_player(interaction, init_player_data)
        if interaction.user in self.game.player_data \
        and interaction.user not in self.game.turn_order:
            self.game.turn_order.append(interaction.user)
        else:
            self.quick_log("Something really weird happened in the uno add_player method")

    async def remove_player(self, interaction):
        '''
        remove_player: Called when a user presses the "Quit" button.
        This method removes the player from the game state's player_data
        and turn_order.
        '''
        await super().remove_player(interaction)
        if interaction.user not in self.game.player_data \
        and interaction.user in self.game.turn_order:
            self.game.turn_order.remove(interaction.user)
        # if nobody else is left, then quit the game
        if self.game.players == 0:
            await self.quit_game(interaction)

    async def start_game(self, interaction):
        '''
        start_game: Called when a person presses the "Start Game"
        button. It changes base_gui to one that is unique for Uno and
        calls the setup() method to setup the game state.
        '''
        if self.game.game_state == 4:
            interaction.response.send_message("This game has already started.",
                                              ephemeral = True, delete_after = 10)
            return
        # game_state == 4 -> players cannot join or leave
        self.game.game_state = 4
        # swap default GUI to active game buttons
        # legacy from pre game state based view system
        #self.base_gui = Views.UnoButtonsBaseGame(self)
        # setup the game board
        await self.setup()
        await self.resend(interaction)

    async def start_new_round(self, interaction):
        """
        start_new_round: Reset the game state to player join phase.
        """
        self.quick_log("Starting a new round of Uno...")
        for player in self.game.turn_order:
            self.game.player_data[player].reset()
        self.game.game_state = 1
        # allow players to join
        #pre game state dict code
        #self.base_gui = UnoButtonsBase(self)
        await self.resend(interaction)

    def get_base_menu_string(self):
        '''
        get_base_menu_string: Used to update the base_gui's message by 
        checking the game state's 'state'.
        '''
        if self.game.game_state == 1:
            return "Welcome to this game of Uno. Feel free to join."
        elif self.game.game_state == 4:
            output = f"Top Card: {self.card_to_emoji(self.game.top_card)} \n\
                It's {current_turn_name}'s turn!\n\
                {next_turn_name}"
            return output
        return "Game has started!"

    async def announce(self, announcement):
        '''
        announce: This method is called whenever there is information that
        needs to be announced to all players, such as:
            a. Player got skipped.
            b. Player got force fed cards.
            c. Player has 1 card remaining in hand.
            d. Player won.
        '''
        await self.channel.send(announcement,
            delete_after=
            self.game.preferences_variables.get_value_of("Announcement lifetime"),
        )

    async def setup(self):
        '''
        setup: Called before allowing the player to actually play a 
        round of Uno. This method sets up the game state by populating
        and shuffling the Uno deck, choosing an appropriate top card 
        ("Reverse", "Skip", "Draw Two", and "Draw Four" cards are not 
        considered appropriate to start the game), choosing a random 
        player to start the game, and having each player draw 7 cards.
        '''
        self.quick_log("Setting up the game of Uno...")
        # Create the deck
        self.game.discard.clear()
        self.game.deck = self.generate_deck()
        random.shuffle(self.game.deck)
        # Each player gets 7 cards to start
        for i in self.game.player_data:
            await self.draw_cards(self.game.player_data[i], 7)
        # Assign the top-card. The game cannot begin on a "Reverse", "Skip", "Draw Two", or "Wild"
        while True:
            self.game.top_card = self.game.deck.pop()
            top_card_is_invalid = False
            match(self.game.top_card.value):
                case "Reverse" | "Skip" | "Draw Two":
                    top_card_is_invalid = True
                case _:
                    match(self.game.top_card.name):
                        case "Wild":
                            top_card_is_invalid = True
            if top_card_is_invalid:
                self.game.discard.append(self.game.top_card)
                continue
            else:
                break
        # Shuffle the ordering and select a random player to start the game
        random.shuffle(self.game.turn_order)
        #technically unnecessary but theres no harm in it
        self.game.turn_index = random.randint(0, len(self.game.turn_order)-1)

    async def draw_cards(self, player, num_cards=1):
        '''
        draw_cards: Takes an UnoPlayer object as an argument, as well 
        as an optional integer, and adds cards to the UnoPlayer's hand
        from the top of the deck. If the deck is empty, this method
        calls regenerate_deck() to replenish it. If an optional integer
        argument is provided, this method adds that many cards to the 
        players hand. Otherwise, it defaults to adding only 1 card.
        '''
        self.quick_log("A player is drawing cards...")
        for _ in range(num_cards):
            if len(self.game.deck) == 0:
                await self.announce("The deck is empty! Shuffling in the discard pile...")
                self.regenerate_deck()
            card = self.game.deck.pop()
            player.hand.append(card)
            player.hand = sorted(player.hand)
        if num_cards == 1:
            return card

    def generate_deck(self):
        '''
        generate_deck: Creates a list of Card objects in accordance with
        the requirements of an Uno deck:
            a. One '0' card for each color 'Red', 'Blue', 'Green', 'Yellow'
            b. Two cards for each color for each number "1-9"
            c. Two cards for each color for each "Skip", "Reverse", and
               "Draw Two".
            d. Four "Wild" cards and four "Wild Draw Four" cards.
            e. Total of 108 cards.
        '''
        deck = []
        for color in ('Red', 'Yellow', 'Green', 'Blue'):
            deck.append(UnoCard(color, '0'))
            for value in range(1,10):
                deck.append(UnoCard(color, str(value)))
                deck.append(UnoCard(color, str(value)))
            for value in range(2):
                deck.append(UnoCard(color, "Draw Two"))
                deck.append(UnoCard(color, "Reverse"))
                deck.append(UnoCard(color, "Skip"))
        for value in range(4):
            deck.append(UnoCard("Wild", "Wild"))
            deck.append(UnoCard("Wild", "Draw Four"))
        return deck

    def regenerate_deck(self):
        '''
        regenerate_deck: This method is called by draw_cards() to 
        replenish the deck when its empty. It simply shuffles the 
        discard pile, adds all the cards in the discard pile to the
        deck, then empties the discard pile.
        '''
        self.quick_log("Regenerating the deck...")
        random.shuffle(self.game.discard)
        self.game.deck += self.game.discard
        self.game.discard.clear()

    def card_to_emoji(self, card):
        '''
        card_to_emoji: Helper method that takes a card as argument and
        returns a string representing the card's color as an emoji.
        The emoji is in colon-flanked-text form.
        '''
        match card.name:
            case "Red":
                return ":red_circle:"
            case "Yellow":
                return ":yellow_circle:"
            case "Green":
                return ":green_circle:"
            case "Blue":
                return ":blue_circle:"
            case "Wild":
                return ":rainbow:"
            case _:
                return "Unknown color, this should not appear."

    def play_card(self, interaction_user, card):
        pass

    def get_playable_cards(self, player_data):
        """
        returns a list of the playable cards from the hand of some given player data
        """
        return [
            card
            for card in player_data.hand if
            self.can_play_card(card)
        ]

    def can_play_card(self, card):
        """
        returns boolean for if the given card could be played on the top card
        """
        if len(self.game.queued_cards) == 0:
            return self.can_play_left_on_right(card, self.game.top_card)
        else:
            return (
                self.can_play_left_on_right(card, self.game.top_card) and
                self.can_stack_effect_of_left_on_right(card, self.game.top_card)
            )

    def get_card_category(self, card):
        """
        finds the category string used in variable values for a given card
        """
        #card type and name to general name categories used in option values dictionary
        #I am sorry and am on 5 hours of sleep, it is taking me 30 seconds to do 17-7.
        card_to_category = {
            ("Wild","Draw Four"): "plus_fours",
        }
        for color in ('Red', 'Yellow', 'Green', 'Blue'):
            card_to_category[(color, "Draw Two")]= "plus_twos"
            card_to_category[(color, "Skip")]= "effect_cards"
            card_to_category[(color, "Reverse")]= "effect_cards"
        if card not in card_to_category:
            return None
        return card_to_category[(card.name,card.value)]

    def is_normal_card(self,card):
        """
        Simple check to see if card falls in the effect, plus two, or plus four card categories
        """
        return self.get_card_category(card) is None

    def can_play_left_on_right(self, left, right):
        """
        returns boolean for if card suite or card name matches
        """
        return (
            left.name == right.name or
            left.value == right.value or
            left.name == "Wild"
        )

    def can_stack_effect_of_left_on_right(self, left, right):
        """
        returns boolean for if a given card would be stackable on the last card in the queue of
        cards to have their effects applied
        """
        return (
            f"can_stack_{self.get_card_category(left)}_on_{self.get_card_category(right)}"
            in self.game.variables.get_value_of("Stacking allowances")
            ) and not self.is_normal_card(left)

    async def end_game(self, interaction):
        """
        Ends the game.
        """
        await self.announce(interaction.user.display_name + " won! Game game, nerds.")
        await self.quit_game(interaction)
