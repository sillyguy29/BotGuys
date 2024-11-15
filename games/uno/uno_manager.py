"""Uno game module

Contains all the logic needed to run a game of Uno.
It features an closed game model, meaning not all users can interact
with the game at any time, and there is player management.
"""
import random
import discord
from games.game import BaseGame
from games.game import GameManager
from games.uno.uno_card import UnoCard
from games.uno.uno_game import UnoGame
from games.uno.uno_player import UnoPlayer
import games.uno.uno_views as Views

from utils.variable_management.variable import IntegerVariable
from utils.variable_management.variable import OptionVariable
from utils.variable_management.variable import BooleanVariable
from utils.variable_management.variable import OptionRepresentation
from utils.variable_management.variable_storage import VariableStorage

#TODO split views into separate file
#TODO separate view for users who can affect it maybe
#TODO implement dismissing preferences menu after game starts
#TODO implement preferences behavior
#TODO disable preferences button after game start
#TODO show settings in join message
#TODO single instance of preferences_gui view may cause issues with dynamic preference adding.
#TODO setup rows for preferences menu to fix annoying ui element ordering
#TODO implement effect stacking
#TODO reimplement UNO from scratch to use new view system

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
            factory=factory
        )
        self.prepare_preferences_quit_button()

    def prepare_preferences_quit_button(self):
        """
        Prepares the games preferences menu for 
        """
        preferences_quit_button = discord.ui.Button(
            style=discord.ButtonStyle.red,
            label="Exit Settings",
        )
        async def quit_button_callback(interaction):
            self.quick_log(f"{interaction.user} pressed {preferences_quit_button.label}!")
            # start the game
            await self.close_preferences_menu(interaction)
        preferences_quit_button.callback = quit_button_callback
        self.preferences_menu.add_ui_element(preferences_quit_button)
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
        self.base_gui = Views.UnoButtonsBaseGame(self)
        # setup the game board
        await self.setup()
        await self.resend(interaction)

    def get_base_menu_string(self):
        '''
        get_base_menu_string: Used to update the base_gui's message by 
        checking the game state's 'state'.
        '''
        if self.game.game_state == 1:
            return "Welcome to this game of Uno. Feel free to join."
        elif self.game.game_state == 4:
            output = f"Top Card: {self.card_to_emoji(self.game.top_card)} \n \
                It's {self.game.turn_order[self.game.turn_index]} turn!"
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

    async def end_game(self, interaction):
        """
        Ends the game.
        """
        await self.announce(interaction.user.display_name + " won! Game game, nerds.")
        await self.quit_game(interaction)
