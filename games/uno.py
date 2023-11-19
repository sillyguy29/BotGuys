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
    def __init__(self):
        super().__init__()
    
        self.hand = []
        self.skipped = False
        
    def get_playable_cards(self, top_card):
        playable_cards = [card for card in self.hand if card.name == top_card.name or card.value == top_card.value or card.name == "Wild"]
        return playable_cards
        
    


class UnoGame(BaseGame):
    """
    Uno game model class. Keeps track of the deck and none else
    """
    def __init__(self):
        # game state 1 -> accepting players but not playing yet
        super().__init__(game_type=3, player_data={}, game_state=1)
        
        self.deck = generate_deck_uno()
        random.shuffle(self.deck)
        self.discard = []
        self.turn_order = []
        self.turn_index = 0
        self.reversed = False
        self.top_card = UnoCard("None", "")
      
        
class UnoManager(GameManager):
    def __init__(self, factory, channel, user_id):
        super().__init__(game=UnoGame(), base_gui=UnoButtonsBase(self),
                         channel=channel, factory=factory)
        
    async def add_player(self, interaction, init_player_data=None):
        await super().add_player(interaction, init_player_data)
        if interaction.user in self.game.player_data \
        and interaction.user not in self.game.turn_order:
            self.game.turn_order.append(interaction.user)

    async def remove_player(self, interaction):
        await super().remove_player(interaction)
        if interaction.user not in self.game.player_data \
        and interaction.user in self.game.turn_order:
            self.game.turn_order.remove(interaction.user)
        # if nobody else is left, then quit the game
        if self.game.players == 0:
            await self.quit_game(interaction)
    
    async def start_game(self, interaction):
        if self.game.game_state == 4:
            interaction.response.send_message("This game has already started.",
                                              ephemeral = True, delete_after = 10)
            return
        # game_state == 4 -> players cannot join or leave
        self.game.game_state = 4
        # swap default GUI to active game buttons
        self.base_gui = UnoButtonsBaseGame(self)
        # setup the game board
        self.setup()
        await self.resend(interaction)
        
    def get_base_menu_string(self):
        if self.game.game_state == 1:
            return "Welcome to this game of Uno. Feel free to join."
        elif self.game.game_state == 4:
            output = f"Top Card: {card_to_emoji(self.game.top_card)} \n It's {self.game.turn_order[self.game.turn_index]} turn!"
            return output
        return "Game has started!"
       
    def setup(self):
        print("Entering setup...")
        # Each player gets 7 cards to start
        for i in self.game.player_data:
            self.draw_cards(self.game.player_data[i], 7)
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

    def draw_cards(self, player, num_cards=1):
        for i in range(num_cards):
            if len(self.game.deck) == 0: 
                self.announce("The deck is empty! Shuffling in the discard pile...")
                self.regenerateDeck()
            card = self.game.deck.pop()
            player.hand.append(card)
            player.hand = sorted(player.hand)
        if num_cards == 1: return str(card)
    
    def get_player_hand(self, player):
        return self.game.player_data[player].hand
    
    def update_turn_index(self):
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
        self.game.discard.append(self.game.top_card)
        self.game.top_card = card
        # If card is "Skip", "Draw Two", or "Draw Four", you will need a victim
        victim_user = self.game.turn_order[self.get_next_turn_index()]
        victim_name = victim_user.display_name
        victim_unoplayer = self.game.player_data[victim_user]
        # If "Reverse" card was played, reverse the queue
        if card.value == "Reverse":
            self.game.reversed = not self.game.reversed
            self.announce("Reversing the turn order!")
        # If "Wild" card is played, inquire what color is next
        if card.name == "Wild":
            view = UnoWildCard(self)
            await interaction.response.send_message("Choose a color!", view = view, ephemeral = True)
        # If "Skip" was played, flag them as 'skipped'
        if card.value == "Skip":
            self.announce(victim_name + " got skipped! LOL!")
            victim_unoplayer.skipped = True
        # If "Draw Two" was played, make next player draw two cards
        #    and then flag them as 'skipped'
        if card.value == "Draw Two":
            self.announce(victim_name + " eats two cards! LMAO!")
            self.draw_cards(victim_unoplayer, 2)
            victim_unoplayer.skipped = True
        # If "Draw Four" was played, make next player draw four cards
        #    and then flag them as 'skipped'
        if card.value == "Draw Four":
            self.announce(victim_name + " eats four cards! ROFL!!")
            self.draw_cards(victim_unoplayer, 4)
            victim_unoplayer.skipped = True
        # Remove the played card from the player's hand
        player = self.game.player_data[interaction.user]
        player.hand.remove(card)
        if len(player.hand) == 1:
            self.announce("Oh fuck! " + player.display_name + " has only one card left!")
        # Go to next turn
        await self.next_turn()

    async def next_turn(self):
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
        await self.channel.send(announcement, delete_after=10)





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
        card_drawn = self.manager.draw_cards(player)
        await interaction.response.send_message("You drew a " + card_drawn, ephemeral = True,
                                                delete_after = 10)
        self.manager.next_turn()
        # delete the response to the card button press (the UnoCardButtons UI message)
        await interaction.delete_original_response()


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
        super().__init__(style=discord.ButtonStyle.gray, label=f"{card.value}", emoji=color_to_emoji(card))
        self.manager = manager
        self.card = card
        self.disabled = disabled
        
    async def callback(self, interaction: discord.Interaction):
        print(f"{interaction.user} pressed {str(self.card)}!")
        assert self.view is not None
        view: UnoCardButtons = self.view
        await self.manager.play_card(interaction, self.card)
        view.stop()
        await interaction.response.send_message(f"You played {str(self.card)}", ephemeral = True,
                                                delete_after = 10)


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
        
    @discord.ui.button(label = "Blue", style = discord.ButtonStyle.gray, emoji = "🔵")
    async def blue(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Chnages the wild card to blue.
        """
        print(f"{interaction.user} pressed {button.label}!")
        
    @discord.ui.button(label = "Yellow", style = discord.ButtonStyle.gray, emoji = "🟡")
    async def yellow(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Chnages the wild card to yellow.
        """
        print(f"{interaction.user} pressed {button.label}!")
        
    @discord.ui.button(label = "Green", style = discord.ButtonStyle.gray, emoji = "🟢")
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Chnages the wild card to green.
        """
        print(f"{interaction.user} pressed {button.label}!")


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
    
    
def generate_deck_uno():
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


def card_to_emoji(card):
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
        output += ":black_circle: "
    output += card.value
    return output


def color_to_emoji(card):
    if card.name == "Red":
        return "🔴"
    elif card.name == "Yellow":
        return "🟡"
    elif card.name == "Green":
        return "🟢"
    elif card.name == "Blue":
        return "🔵"
    elif card.name == "Wild":
        return "⚫"
    return "🟣"


