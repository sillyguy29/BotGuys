"""Uno game module

Contains all the logic needed to run a game of Uno.
It features an closed game model, meaning not all users can interact
with the game at any time, and there is player management.
"""
import random
import discord
from games.game import BaseGame
from games.game import GameManager
from games.game import BasePlayer
from util import Card

#TODO split views into separate file
#TODO implement getters and setters for preferences, possibly some sort of name and type association system for preferences
#TODO implement dynamic preferences menu generation
#TODO separate view for users who can affect it maybe
#TODO implement dismissing preferences menu after game starts
#TODO implement actual settings menu
#TODO implement preferences behavior
#TODO disable preferences button after game start
#TODO show settings in join message
#TODO single instance of preferences_gui view may cause issues with dynamic preference adding.
#TODO setup rows for preferences menu to fix annoying ui element ordering

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

    def get_playable_cards(self, top_card):
        """
        Used by the button menu to determine which cards can be
        enabled.
        """
        playable_cards = [card for card in self.hand if card.name == top_card.name \
            or card.value == top_card.value or card.name == "Wild" ]
        return playable_cards


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
        #preferences variables
        self.preferences = {
            "Drawn card show time": {"type": "number", "value": 5, "min": 0, "max": 20},
            "Make deck time":       {"type": "number", "value": 0, "min": 0, "max": 20},
            "Stacking allowances":  {
                "type": "select", 
                "value": [
                    "can_stack_effect_cards_on_effect_cards",
                    "can_stack_plus_fours_on_effect_cards",
                    "can_stack_effect_cards_on_plus_fours",
                    "can_stack_plus_fours_on_plus_fours"
                ],
                "options": [
                    {
                        "value": "can_stack_effect_cards_on_effect_cards", 
                        "label": "Can stack effect cards on other effect cards"
                    },
                    {
                        "value": "can_stack_plus_fours_on_effect_cards",
                        "label": "Can stack plus fours on effect cards"
                    },
                    {
                        "value": "can_stack_effect_cards_on_plus_fours",
                        "label": "Can stack effect cards on plus fours"
                    },
                    {
                        "value": "can_stack_plus_fours_on_plus_fours",
                        "label": "Can stack plus fours on other plus fours"
                    }
                ],
                "min_selected": 0,
                "max_selected": 4
            },
            "Reverse card repeats players turn":              {"type" : "boolean", "value": False},
            "Can callout Uno":                                {"type" : "boolean", "value": False},
            "Can only play plus fours without matching color":{"type" : "boolean", "value": False},
        }
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

class UnoManager(GameManager):
    '''
    Uno game model class that controls the flow of Uno by interacting
    and modifying its UnoGame property and updating its base GUI to
    receive input from the players.
    '''
    def __init__(self, factory, channel, user_id=None):
        super().__init__(
            game=UnoGame(user_id),
            base_gui=UnoButtonsBase(self),
            channel=channel,
            factory=factory,
            preferences_gui=UnoButtonsPreferences(self)
        )

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

    def add_menu_items(self, view):
        """
        Adds the ui elements needed to change the preferences of a managers game to a view
        """
        for key,value in self.game.preferences.items():
            if value["type"] == "number":
                generated_button = discord.ui.Button(
                    label=f"{key} is {value['value']}"
                )
                generated_modal = discord.ui.Modal(
                    title=key
                )
                generated_modal.add_item(discord.ui.TextInput(
                    label=key,
                    placeholder="Enter a number...",
                    default=str(value["value"]),
                    min_length=len(str(value["min"])),
                    max_length=len(str(value["max"]))
                ))
                async def set_value_from_modal(
                    interaction, modal_in_question=generated_modal,
                    value=value["value"]
                    ):
                    value = int(modal_in_question.children[0].value)
                    modal_in_question.stop()
                    await interaction.response.send_message(
                        content="Response",
                        silent=True,
                        ephemeral=True,
                        delete_after=0
                    )
                async def interaction_check_for_modal(
                    interaction,
                    modal_in_question=generated_modal
                    ):
                    try:
                        int(modal_in_question.children[0].value)
                    except ValueError:
                        return False
                    return True
                generated_modal.interaction_check = interaction_check_for_modal
                generated_modal.on_submit = set_value_from_modal
                async def bring_up_modal(
                    interaction,
                    modal_to_use=generated_modal
                    ):
                    await interaction.response.send_modal(modal_to_use)
                generated_button.callback = bring_up_modal
                view.add_item(generated_button)
            elif value["type"] == "select":
                generated_select_menu = discord.ui.Select(
                    min_values = value["min_selected"],
                    max_values = value["max_selected"],
                    options = [
                        discord.SelectOption(
                            label = x["label"],
                            value = x["value"],
                            default = x["value"] in value["value"]
                        )
                        for x in value["options"]
                    ]
                    #list comprehension for turning all options listed in
                    #preferences options into selectionOption items
                )
                #generated_select_menu.callback = lambda interaction: interaction.
                # response.send_message()
                view.add_item(generated_select_menu)
            elif value["type"] == "boolean":
                #Similar to the select type but specifically for boolean values.
                #The naming could be better then just shoving the key name into
                #the label but it would require specifying it in the preferences dict.
                generated_boolean_menu = discord.ui.Select(
                    min_values = 1,
                    max_values = 1,
                    options = [
                        discord.SelectOption(
                            label = f"{key} Enabled",
                            value = "True",
                            default = value["value"]
                        ),
                        discord.SelectOption(
                            label = f"{key} Disabled",
                            value = "False",
                            default = not value["value"]
                        )
                    ]
                )
                view.add_item(generated_boolean_menu)
            else:
                raise ValueError("Invalid preference type in game")

    async def preferences_menu(self, interaction):
        """
        This is the uno manager call for preferences menu
        If the user that called for the preferences menu is the one who called the
        uno command and is currently in the game and game has not started
        send an ephemeral message to the person who called for the preferences menu
        which contains the submenu for selecting Uno Settings. Otherwise send a failure
        message mentioning one of these requirements. The preferences menu will stay until
        the user dismisses it or the game starts.
        """
        if  self.game.game_state != 4 and \
            interaction.user in self.game.player_data and \
            interaction.user in self.game.turn_order and \
            interaction.user.id == self.game.user_id:
            self.add_menu_items(self.preferences_gui)
            await interaction.response.send_message(
                content="",
                view=self.preferences_gui,
                silent=True,
                ephemeral=True,
                delete_after=60
            )
        elif interaction.user.id != self.game.user_id:
            await interaction.response.send_message(
                content="You are not the creator of this game.",
                silent=True,
                ephemeral=True,
                delete_after=5
            )
        elif interaction.user not in self.game.player_data:
            await interaction.response.send_message(
                content="You have not yet joined the game.",
                silent=True,
                ephemeral=True,
                delete_after=5
            )
        elif interaction.user in self.game.turn_order:
            await interaction.response.send_message(
                content="You have not yet joined the game.",
                silent=True,
                ephemeral=True,
                delete_after=5
            )


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
        self.base_gui = UnoButtonsBaseGame(self)
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

    async def start_new_round(self, interaction):
        """
        start_new_round: Reset the game state to player join phase.
        """
        self.quick_log("Starting a new round of Uno...")
        for player in self.game.turn_order:
            self.game.player_data[player].reset()
        self.game.game_state = 1
        # allow players to join
        self.base_gui = UnoButtonsBase(self)
        await self.resend(interaction)

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
            top_card_is_valid = True
            if self.game.top_card.value == "Reverse":
                top_card_is_valid = False
            if self.game.top_card.value == "Skip":
                top_card_is_valid = False
            if self.game.top_card.value == "Draw Two":
                top_card_is_valid = False
            if self.game.top_card.name == "Wild":
                top_card_is_valid = False
            if not top_card_is_valid:
                self.game.discard.append(self.game.top_card)
                continue
            else:
                break
        # Shuffle the ordering and select a random player to start the game
        random.shuffle(self.game.turn_order)
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

    def get_player_hand(self, player):
        '''
        get_player_hand: Easy method to see player's hand.
        '''
        return self.game.player_data[player].hand

    def update_turn_index(self):
        '''
        update_turn_index: Called after a player plays a card. This
        method increments or decrements the game state's turn_index 
        depending on if the game state is reversed or not. This method
        also returns the turn_index to the beginning or end of the 
        turn_order if incrementing/decrementing would exceed boundaries.
        '''
        index = self.game.turn_index
        if not self.game.reversed:
            index += 1
            if index == len(self.game.turn_order):
                index = 0
            self.game.turn_index = index
        elif self.game.reversed:
            index -= 1
            if index == -1:
                index = len(self.game.turn_order) - 1
            self.game.turn_index = index

    def get_next_turn_index(self):
        '''
        get_next_turn_index: This method tells us who the next player
        is by returning an integer that would be the next turn_index,
        taking into account whether the game state is reversed or not.
        This method is called when a player plays a "Skip", "Draw Two",
        and "Draw Four" card to determine which UnoPlayer object needs
        to be flagged as 'skipped', as well as forcing feeding that 
        player some cards on "Draw Two" and "Draw Four".
        '''
        next_player = self.game.turn_index
        if not self.game.reversed:
            next_player += 1
            if next_player == len(self.game.turn_order):
                next_player = 0
            return next_player
        elif self.game.reversed:
            next_player -= 1
            if next_player == -1:
                next_player = len(self.game.turn_order) - 1
            return next_player

    async def play_card(self, interaction, card):
        '''
        play_card: This method is called when a player presses a 
        button corresponding to a card in their hand. It takes the
        interaction and the corresponding card as arguments. The top card 
        is replaced with that card (unless the card is Wild, then we do 
        it differently). Then, depending on the card, this method branches 
        off into different cases: 
            a. "Wild": Prompt the player to choose a color by giving
            them a new button menu. The new menu will replace the top
            card with a placeholder card that has no value but does 
            have the color chosen by the player.
            b. "Skip": Determine next player and flag them as 'skipped'
            c. "Reverse": Switch the game state's 'reversed' property.
            d. "Draw Two": Skip next player and force feed two cards.
            e. "Draw Four": Skip next player and force feed four cards.
        At the end of this method, we remove the card from the player's hand,
        performing a few checks in the process:
            i. Player has 1 card remaining: Announce this fact to all players
            ii. Player has 0 cards remaining: This player won. End the game.
        Finally, if the game didn't end, then we call next_turn() to allow
        the next player to play a card.

        This method very much upholds the 'God Function' trope. Refactoring may
        be desired in this area.
        '''
        self.quick_log("A player is playing a card...")
        # We put add the top card to the discard pile,
        # but only if it's not a placeholder card
        if self.game.top_card.value != "Card":
            self.game.discard.append(self.game.top_card)
        # Then we can replace the top card with the played card, unless it's wild
        if card.name == "Wild":
            view = UnoWildCard(self) # Menu to inquire what the next card is
            await interaction.response.send_message("Choose a color!", view = view, \
                ephemeral=True, delete_after=10)
            await view.wait()
            await interaction.delete_original_response()
        else: # Not wild, just replace
            self.game.top_card = card
        # If card is "Skip", "Draw Two", or "Draw Four", you will need a victim
        victim_user = self.game.turn_order[self.get_next_turn_index()]
        victim_name = victim_user.display_name
        victim_unoplayer = self.game.player_data[victim_user]
        # If "Reverse" card was played, reverse the queue
        if card.value == "Reverse":
            self.game.reversed = not self.game.reversed
            await self.announce("Reversing the turn order!")
        # If "Skip" was played, flag them as 'skipped'
        if card.value == "Skip":
            await self.announce(victim_name + " got skipped! LOL!")
            victim_unoplayer.skipped = True
        # If "Draw Two" was played, make next player draw two cards
        #    and then flag them as 'skipped'
        if card.value == "Draw Two":
            await self.announce(victim_name + " eats two cards! LMAO!")
            await self.draw_cards(victim_unoplayer, 2)
            victim_unoplayer.skipped = True
        # If "Draw Four" was played, make next player draw four cards
        #    and then flag them as 'skipped'
        if card.value == "Draw Four":
            await self.announce(victim_name + " eats four cards! ROFL!!")
            await self.draw_cards(victim_unoplayer, 4)
            victim_unoplayer.skipped = True
        # Remove the played card from the player's hand
        player = self.game.player_data[interaction.user]
        player.hand.remove(card)
        if len(player.hand) == 1:
            await self.announce("Oh fuck! " + interaction.user.display_name + \
                " has only one card left!")
        if len(player.hand) == 0:
            await self.end_game(interaction)
            return
        # Go to next turn
        await self.next_turn()


    async def next_turn(self):
        '''
        next_turn: This method calls the update_turn_index() several times,
        skipping over 'skipped' players and restoring the flag to default, 
        until a player that is not flagged as 'skipped' is discovered. Then,
        this method refreshes the base GUI so the new player can take their
        turn.
        '''
        self.quick_log("Going to the next turn...")
        # Increment (or decrement if turn order reversed) the turn index
        self.update_turn_index()

        # Check if player is skipped. If so, move on to the next player
        next_player = self.game.player_data[self.game.turn_order[self.game.turn_index]]
        while next_player.skipped:
            next_player.skipped = False
            self.update_turn_index()
            next_player = self.game.player_data[self.game.turn_order[self.game.turn_index]]

        # Refresh the base GUI
        await self.current_active_menu.edit(content=self.get_base_menu_string(),
                                            view=self.base_gui)

    async def announce(self, announcement):
        '''
        announce: This method is called whenever there is information that
        needs to be announced to all players, such as:
            a. Player got skipped.
            b. Player got force fed cards.
            c. Player has 1 card remaining in hand.
            d. Player won.
        '''
        await self.channel.send(announcement, delete_after=3)

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


    def card_to_emoji(self, card):
        '''
        card_to_emoji: Helper method that takes a card as argument and
        returns a string representing the card's color as an emoji.
        The emoji is in colon-flanked-text form. 

        It is uncertain if this method is redundant with color_to_emoji.
        Refactoring may be desired in this area.
        '''
        output = ""
        if card.name == "Red":
            output += ":red_circle: "
        elif card.name == "Yellow":
            output += ":yellow_circle: "
        elif card.name == "Green":
            output += ":green_circle: "
        elif card.name == "Blue":
            output += ":blue_circle: "
        elif card.name == "Wild":
            output += ":rainbow: "
        output += card.value
        return output


    def color_to_emoji(self, card):
        '''
        color_to_emoji: Helper method that takes a card as argument and
        returns a string representating the card's color as an emoji.
        The emoji is in actual-emoji form.

        It is uncertain if this method is redundant with color_to_emoji.
        Refactoring may be desired in this area.
        '''
        if card.name == "Red":
            return "🔴"
        elif card.name == "Yellow":
            return "🟡"
        elif card.name == "Green":
            return "🟢"
        elif card.name == "Blue":
            return "🔵"
        elif card.name == "Wild":
            return "🌈"
        return "🟣"

    async def end_game(self, interaction):
        """
        Ends the game.
        """
        await self.announce(interaction.user.display_name + " won! Game game, nerds.")
        await self.quit_game(interaction)



         #######################################################
      ####                                                     ####
    ###                      BUTTON STUFF                         ###
      ####                                                     ####
         #######################################################

class UnoButtonsBase(discord.ui.View):
    """
    Base menu button group for the Uno game.
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "Join", style = discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Send an ephemeral message to the person who interacted with
        this button that contains the hit or miss menu. This menu
        will be deleted after it is interacted with or 10 seconds
        has passed (prevents menus that are not accounted for after
        game end).
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        await self.manager.add_player(interaction)

    @discord.ui.button(label="Settings", style= discord.ButtonStyle.blurple)
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        If the user that interacted with this menu is currently in the game, send
        an ephemeral message to the person who interacted with this
        menu a message which contains the submenu for selecting Uno Settings until
        the user dismisses it or the game starts or ends, otherwise do nothing.
        """
        self.manager.quick_log(f"{interaction.user} pressed {button.label}")
        await self.manager.preferences_menu(interaction)

    @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Quit the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        # remove current players from active player list
        await self.manager.remove_player(interaction)

    @discord.ui.button(label = "Start Game", style = discord.ButtonStyle.blurple)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Start the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        # start the game
        await self.manager.start_game(interaction)

class UnoButtonsPreferences(discord.ui.View):
    """
    Provides the menu for adjusting uno settings on a per player basis
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "Placeholder button", style = discord.ButtonStyle.blurple)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        A place holder button for use until the uno preferences menu has actual
        settings management implemented.
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        # start the game
        #await self.manager.start_game(interaction)

    @discord.ui.button(label = "Exit Settings", style = discord.ButtonStyle.red)
    async def exit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        A place holder button for use until the uno preferences menu has actual
        settings management implemented.
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        # start the game
        await self.manager.close_preferences_menu(interaction)

class UnoButtonsBaseGame(discord.ui.View):
    """
    Menu includes "Show Hand" and "Draw"
    In the future: Include "Quit" button here as well.
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "Show Hand", style = discord.ButtonStyle.green)
    async def show_cards(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Send an ephemeral message to the person who interacted with
        this button that contains the show cards menu. This menu
        will be deleted after it is interacted with or 20 seconds
        has passed (prevents menus that are not accounted for after
        game end).
        """

        # Delete prior "Show Hand" menu so there isn't several lingering
        uno_player = self.manager.game.player_data[interaction.user]
        if uno_player.active_interaction:
            await uno_player.active_interaction.delete_original_response()
            uno_player.active_interaction = None

        # Send user a new "Show Hand" menu
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        view = UnoCardButtons(self.manager, interaction.user)
        await interaction.response.send_message("Your cards:", view = view, ephemeral = True)

        # We track this interaction so we can delete the message if player presses "Draw"
        #    rather than waiting for the message to delete itself after 20 seconds
        self.manager.game.player_data[interaction.user].active_interaction = interaction
        # wait for the view to call self.stop() before we move beyond this point
        await view.wait()
        # delete the response to the card button press (the UnoCardButtons UI message)
        await interaction.delete_original_response()
        self.manager.game.player_data[interaction.user].active_interaction = None

    @discord.ui.button(label = "Draw", style = discord.ButtonStyle.blurple)
    async def draw_card(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Sends a ephemeral message to the person who interacted with
        this button to inform him of what card he draw.
        """
        # Reject request to draw cards if button presser is not the current turn player
        current_turn_player = self.manager.game.turn_order[self.manager.game.turn_index]
        if interaction.user != current_turn_player:
            await interaction.response.send_mesage("Wait your turn.", ephemeral = True, \
                delete_after = 2)
            return

        # If there is an active "Show Hand" menu, we should delete it now
        uno_player = self.manager.game.player_data[interaction.user]
        if uno_player.active_interaction:
            await uno_player.active_interaction.delete_original_response()
            uno_player.active_interaction = None

        # If the button presser IS the turn player, do the following:
        player = self.manager.game.player_data[interaction.user]
        card_drawn = await self.manager.draw_cards(player)
        msg = button.label + "! You drew a " + self.manager.color_to_emoji(card_drawn) \
            + " " + card_drawn.value
        await interaction.response.send_message(msg, ephemeral = True, delete_after = 2)

        # Announce that player has opted to draw a card and proceed to next turn
        await self.manager.announce(str(interaction.user) + " is drawing a card...")
        await self.manager.next_turn()




class UnoCardButtons(discord.ui.View):
    """
    Creates private group of buttons representing the cards in a user's hand
    """
    def __init__(self, manager, player):
        super().__init__()
        self.manager = manager
        self.player_hand = self.manager.get_player_hand(player)
        self.disabled_view = None

        for card in self.player_hand:
            current_turn_player = self.manager.game.turn_order[self.manager.game.turn_index]
            uno_player = self.manager.game.player_data[player]
            playable_cards = uno_player.get_playable_cards(self.manager.game.top_card)
            disabled = (player != current_turn_player) or (card not in playable_cards)
            self.add_item(CardButton(self.manager, card, disabled))



class CardButton(discord.ui.Button):
    """
    Button class that represents an individual card in a user's hand
    """
    def __init__(self, manager, card, disabled=True):
        super().__init__(style=discord.ButtonStyle.gray, label=f"{card.value}", \
            emoji=manager.color_to_emoji(card))
        self.manager = manager
        self.card = card
        self.disabled = disabled

    async def callback(self, interaction: discord.Interaction):
        self.manager.quick_log(f"{interaction.user} pressed {str(self.card)}!")
        assert self.view is not None
        view: UnoCardButtons = self.view
        await self.manager.play_card(interaction, self.card)
        view.stop()


class UnoWildCard(discord.ui.View):
    """
    This is the menu that appears when the player plays a Wild card
    to prompt them to select a color for the next card.
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "Red", style = discord.ButtonStyle.gray, emoji = "🔴")
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Changes the wild card to red.
        """
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        self.manager.game.top_card = Card("Red", "Card")
        self.stop()

    @discord.ui.button(label = "Blue", style = discord.ButtonStyle.gray, emoji = "🔵")
    async def blue(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Changes the wild card to blue.
        """
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        self.manager.game.top_card = Card("Blue", "Card")
        self.stop()

    @discord.ui.button(label = "Yellow", style = discord.ButtonStyle.gray, emoji = "🟡")
    async def yellow(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Changes the wild card to yellow.
        """
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        self.manager.game.top_card = Card("Yellow", "Card")
        self.stop()

    @discord.ui.button(label = "Green", style = discord.ButtonStyle.gray, emoji = "🟢")
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Changes the wild card to green.
        """
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        self.manager.game.top_card = Card("Green", "Card")
        self.stop()


class QuitGameButton(discord.ui.View):
    """
    Button set that asks players if they want to play the game again
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "Go Again!", style = discord.ButtonStyle.green)
    async def restart(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Start a new round
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        # stop accepting input
        self.stop()
        await self.manager.start_new_round(interaction)

    @discord.ui.button(label = "End Game", style = discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Quit the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        # stop accepting input
        self.stop()
        await interaction.channel.send(f"{interaction.user.mention} ended the game!")
        await self.manager.quit_game(interaction)


class UnoCard(Card):
    """
    This class represents an Uno card. On construction, it uses its
    name and value to establish a priority, used for sorting in a list.
    """

    def __str__(self):
        return f"{self.name} {self.value}"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        if self.name != other.name:
            return False
        if self.value != other.value:
            return False
        return True

    def __lt__(self, other):
        if self.name != other.name:
            return self.name < other.name
        return self.value < other.value

    def __gt__(self, other):
        #return self.priority > other.priority
        if self.name != other.name:
            return self.name > other.name
        return self.value > other.value
