"""Uno game module

Contains all the logic needed to run a game of Uno.
It features an closed game model, meaning not all users can interact
with the game at any time, and there is player management.
"""
import discord
from games.game import BaseGame
from games.game import GameManager
from games.game import BasePlayer
from util import Card
import random


class UnoPlayer(BasePlayer):
    """
    Represents an player of the uno game. Extended from the BasePlayer
    class to include a few extra attributes: a list that represents
    the player's hand, a boolean to flag when the player has been 
    skipped, and a method to determine which cards in the player's 
    hand are playable given the game state's top card.
    """
    def __init__(self):
        super().__init__()
    
        self.hand = []
        self.skipped = False
        
    def get_playable_cards(self, top_card):
        playable_cards = [card for card in self.hand if card.name == top_card.name or card.value == top_card.value or card.name == "Wild"]
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
    def __init__(self):
        # game state 1 -> accepting players but not playing yet
        super().__init__(game_type=3, player_data={}, game_state=1)
        
        self.deck = []
        self.discard = []
        self.turn_order = []
        self.turn_index = 0
        self.reversed = False
        self.top_card = UnoCard("None", "")
      
        
class UnoManager(GameManager):
    '''
    Uno game model class that controls the flow of Uno by interacting
    and modifying its UnoGame property and updating its base GUI to
    receive input from the players. A brief overview of its methods:
    1. add_player: adds player to the game
    2. remove_player: removes player from the game
    3. start_game: proceeds to game setup
    4. get_base_menu_string: gets current game message
    5. start_new_round: return to "player join" phase
    6. setup: Sets up the table and players' hands
    7. draw_cards: Gives player cards from the deck
    8. regenerate_deck: Replenishes the deck when its empty
    9. get_player_hand: Handy getter of a player's hand
    10. update_turn_index: Increment or decrement turn index
    11. get_next_turn_index: Tells what the current turn index is
    12. play_card: Handles events of playing a card
    13. next_turn: Update turn index, skipping 'skipped' players
    14. announce: Gives each player important information
    15. card_to_emoji: Returns emoji of a card (colon-flanked-text)
    16. color_to_emoji: Returns emoji of a card (actual-emoji)
    '''
    def __init__(self, factory, channel):
        super().__init__(game=UnoGame(), base_gui=UnoButtonsBase(self),
                         channel=channel, factory=factory)
        
    async def add_player(self, interaction, init_player_data=None):
        '''
        add_player: Called when a person presses the "Join" button.
        This method add the member to the game state's player_data as 
        well as adding their interaction.user to the turn_order.
        '''
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
            output = f"Top Card: {self.card_to_emoji(self.game.top_card)} \n It's {self.game.turn_order[self.game.turn_index]} turn!"
            return output
        return "Game has started!"
       
    async def start_new_round(self, interaction):
        """
        start_new_round: Reset the game state to player join phase.
        """
        for player in self.game.turn_order:
            self.game.player_data[player].reset()
        self.game.turn_index = 0
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
        print("Entering setup...")
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
            if (self.game.top_card.value == "Reverse"): top_card_is_valid = False
            if (self.game.top_card.value == "Skip"): top_card_is_valid = False
            if (self.game.top_card.value == "Draw Two"): top_card_is_valid = False
            if (self.game.top_card.name == "Wild"): top_card_is_valid = False
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
        for i in range(num_cards):
            if len(self.game.deck) == 0: 
                await self.announce("The deck is empty! Shuffling in the discard pile...")
                self.regenerate_deck()
            card = self.game.deck.pop()
            player.hand.append(card)
            player.hand = sorted(player.hand)
        if num_cards == 1: return card
    
    def regenerate_deck(self):
        '''
        regenerate_deck: This method is called by draw_cards() to 
        replenish the deck when its empty. It simply shuffles the 
        discard pile, adds all the cards in the discard pile to the
        deck, then empties the discard pile.
        '''
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
        # We put add the top card to the discard pile, 
        # but only if it's not a placeholder card        
        if (self.game.top_card.value != "Card"):
            self.game.discard.append(self.game.top_card)
        # Then we can replace the top card with the played card, unless it's wild
        if (card.name == "Wild"): 
            view = UnoWildCard(self) # Menu to inquire what the next card is
            await interaction.response.send_message("Choose a color!", view = view, ephemeral=True, delete_after=10)
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
            await self.announce("Oh fuck! " + interaction.user.display_name + " has only one card left!")
        if len(player.hand) == 0:
            await self.announce(interaction.user.display_name + " won! Game game, nerds.")
            #self.quit_game(interaction)
            # then initiate the endgame phase
            self.game.game_state = 7
            restart_ui = QuitGameButton(self)
            active_msg = await self.channel.send("Play again?", view=restart_ui)
            await restart_ui.wait()
            await active_msg.edit(view=None)
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
        await self.channel.send(announcement, delete_after=10)

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
        print(f"{interaction.user} pressed {button.label}!")

        indi_player_data = UnoPlayer()
        await self.manager.add_player(interaction, indi_player_data)
    
    @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Quit the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # remove current players from active player list
        await self.manager.remove_player(interaction)
    
    @discord.ui.button(label = "Start Game", style = discord.ButtonStyle.blurple)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Start the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # start the game
        await self.manager.start_game(interaction)


class UnoButtonsBaseGame(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        
    @discord.ui.button(label = "Show Hand", style = discord.ButtonStyle.green)
    async def show_cards(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Send an ephemeral message to the person who interacted with
        this button that contains the show cards menu. This menu
        will be deleted after it is interacted with or 20 seconds
        has passed (prevents menus that are not accounted for after
        game end).
        """
        print(f"{interaction.user} pressed {button.label}!")
        
        view = UnoCardButtons(self.manager, interaction.user)
        await interaction.response.send_message("Your cards:", view = view, ephemeral = True,
                                                delete_after = 20)
        # wait for the view to call self.stop() before we move beyond this point
        await view.wait()
        # delete the response to the card button press (the UnoCardButtons UI message)
        await interaction.delete_original_response()

    @discord.ui.button(label = "Draw", style = discord.ButtonStyle.blurple)
    async def draw_card(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Sends a ephemeral message to the person who interacted with
        this button to inform him of what card he draw.
        """
        player = self.manager.game.player_data[interaction.user]
        card_drawn = await self.manager.draw_cards(player)
        await interaction.response.send_message("You drew a " + self.manager.color_to_emoji(card_drawn) + " " + card_drawn.value, ephemeral = True,
                                                delete_after = 2)
        await self.manager.next_turn()


class UnoCardButtons(discord.ui.View):
    """
    Creates private group of buttons representing the cards in a user's hand
    """
    def __init__(self, manager, player):
        super().__init__()
        self.manager = manager
        self.player_hand = self.manager.get_player_hand(player)
        
        for i in range(len(self.player_hand)):
            current_turn_player = self.manager.game.turn_order[self.manager.game.turn_index]
            this_card = self.player_hand[i]
            playable_cards = self.manager.game.player_data[player].get_playable_cards(self.manager.game.top_card)
            disabled = (player != current_turn_player) or (this_card not in playable_cards)
            self.add_item(CardButton(self.manager, self.player_hand[i], disabled))

  
class CardButton(discord.ui.Button):
    """
    Button class that represents an individual card in a user's hand
    """
    def __init__(self, manager, card, disabled=True):
        super().__init__(style=discord.ButtonStyle.gray, label=f"{card.value}", emoji=manager.color_to_emoji(card))
        self.manager = manager
        self.card = card
        self.disabled = disabled
        
    async def callback(self, interaction: discord.Interaction):
        print(f"{interaction.user} pressed {str(self.card)}!")
        assert self.view is not None
        view: UnoCardButtons = self.view
        await self.manager.play_card(interaction, self.card)
        view.stop()


class UnoWildCard(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        
    @discord.ui.button(label = "Red", style = discord.ButtonStyle.gray, emoji = "🔴")
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Chnages the wild card to red.
        """
        print(f"{interaction.user} pressed {button.label}!")
        self.manager.game.top_card = Card("Red", "Card")
        self.stop()
        
    @discord.ui.button(label = "Blue", style = discord.ButtonStyle.gray, emoji = "🔵")
    async def blue(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Chnages the wild card to blue.
        """
        print(f"{interaction.user} pressed {button.label}!")
        self.manager.game.top_card = Card("Blue", "Card")
        self.stop()
        
    @discord.ui.button(label = "Yellow", style = discord.ButtonStyle.gray, emoji = "🟡")
    async def yellow(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Chnages the wild card to yellow.
        """
        print(f"{interaction.user} pressed {button.label}!")
        self.manager.game.top_card = Card("Yellow", "Card")
        self.stop()
        
    @discord.ui.button(label = "Green", style = discord.ButtonStyle.gray, emoji = "🟢")
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Chnages the wild card to green.
        """
        print(f"{interaction.user} pressed {button.label}!")
        self.manager.game.top_card = Card("Green", "Card")
        self.stop()


class QuitGameButton(discord.ui.View):
    """
    Button set that asks players if they want to play the game again
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    @discord.ui.button(label = "Go Again!", style = discord.ButtonStyle.green)
    async def restart(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Start a new round
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
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
        print(f"{interaction.user} pressed {button.label}!")
        # stop eccepting input
        self.stop()
        await interaction.channel.send(f"{interaction.user.mention} ended the game!")
        await self.manager.quit_game(interaction)


class UnoCard(Card):
    def __init__(self, name, value):
        super().__init__(name, value)
        
        self.priority = 0
        if self.name == "Red": self.priority += 0
        if self.name == "Blue": self.priority += 15
        if self.name == "Green": self.priority += 30
        if self.name == "Yellow": self.priority += 45
        if self.name == "Wild": self.priority += 60

        if self.value == "Reverse": self.priority += 11
        elif self.value == "Skip": self.priority += 12
        elif self.value == "Draw Two": self.priority += 13
        elif self.value == "Card": self.priority += 1
        elif self.value == "Draw Four": self.priority += 2
        elif self.value == "Wild": self.priority += 0
        elif self.value == "": self.priority += 0
        else: self.priority += int(self.value)
    
    def __str__(self):
        return f"{self.name} {self.value}"
    
    def __eq__(self, other):
        if not isinstance(other, Card): return False
        if self.name != other.name: return False
        if self.value != other.value: return False
        return True
    
    def __lt__(self, other):
        return self.priority < other.priority

    def __gt__(self, other):
        return self.priority > other.priority
    
    

