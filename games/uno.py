"""Uno game module

Contains all the logic needed to run a game of Uno.
It features an closed game model, meaning not all users can interact
with the game at any time, and there is player management.
"""
import discord
from games.game import BaseGame
from games.game import GameManager
from util import Card
#from util import generate_deck_Uno
import random


class UnoGame(BaseGame):
    """
    Uno game model class. Keeps track of the deck and none else
    """
    def __init__(self):
        # game state 1 -> accepting players but not playing yet
        super().__init__(game_type=3, player_data={}, game_state=1)
        
        self.deck = generate_deck_Uno()
        random.shuffle(self.deck)
        self.discard = []
        self.players = []
        self.top_card = UnoCard("None", "")
      
        
class UnoManager(GameManager):
    def __init__(self, factory, channel_id, user_id):
        super().__init__(UnoGame(), UnoButtonsBase(self),
                         channel_id, factory)
        
        # What is player_list? We have player_data (dict) in the game model
        #self.game.player_list.append(user_id)
        
        self.setup()

    #async def create_game(self, interaction):
    #    raise NotImplementedError("Override this method based on uno specifications")
    
    async def start_game(self, interaction):
        # game_state == 4 -> players cannot join or leave
        self.game.game_state = 4
        await self.gameplay_loop()
        
    def get_base_menu_string(self):
        if self.game.game_state == 1:
            return "Welcome to this game of Uno. Feel free to join."
        elif self.game.game_state == 4:
            return "Game has started!"
        
    def setup(self):
        for i in range(1, 6):
            self.game.players.append(Player(f"Player {i}"))
        
        # Draw 7 cards for each player
        for player in self.game.players:
            self.draw_cards(player,7)

        # Assign the top-card. The game cannot begin on a "Reverse", "Skip", "Draw Two", or "Wild"
        print()
        print("Setting up the table...")
        while True:
            self.game.top_card = self.game.deck.pop()
            print(f"The top card is {self.game.top_card}. ", end="")
            top_card_is_valid = True
            if (self.game.top_card.value == "Reverse"): top_card_is_valid = False
            if (self.game.top_card.value == "Skip"): top_card_is_valid = False
            if (self.game.top_card.value == "Draw Two"): top_card_is_valid = False
            if (self.game.top_card.name == "Wild"): top_card_is_valid = False
            if not top_card_is_valid: 
                print("That's no good... Picking a new top card...")
            else:
                print("Let the game begin!")
                break
            
    def draw_cards(self, player, num_cards=1):
        for i in range(num_cards):
            if len(self.game.deck) == 0: 
                self.announce("The deck is empty! Regenerating deck...")
                self.regenerateDeck()
            card = self.game.deck.pop()
            player.hand.append(card)
            player.hand = sorted(player.hand)
    
    def get_player_hand(self, index):
        return self.game.players[index].hand

  
class CardButton(discord.ui.Button):
    """
    Custom button that represents an individual card in a user's hand
    """
    def __init__(self, manager, card_name):
        super().__init__(style=discord.ButtonStyle.gray, label=f"{card_name}")
        self.manager = manager
        self.card_name = card_name
        
    async def callback(self, interaction: discord.Interaction):
        print(f"{interaction.user} pressed {self.label}!")
        assert self.view is not None
        view: UnoCardButtons = self.view
    
        self.disabled = True
        
        view.stop()
                
        await interaction.response.send_message(f"You played {self.label}", ephemeral = True,
                                                delete_after = 10)
 
 
class UnoCardButtons(discord.ui.View):
    """
    Creates private group of buttons to user representing their cards in hand
    """
    def __init__(self, manager, cards_num):
        super().__init__()
        self.manager = manager
        self.cards_num = cards_num
        
        for i in range(self.cards_num):
            # example of what can be done
            self.add_item(CardButton(self.manager, self.manager.get_player_hand(0)[i]))
 
        
class UnoButtonsBase(discord.ui.View):
    """
    Base menu button group for the counter game.
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
    
    @discord.ui.button(label = "Show Cards", style = discord.ButtonStyle.green)
    async def show_cards(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Send an ephemeral message to the person who interacted with
        this button that contains the show cards menu. This menu
        will be deleted after it is interacted with or 60 seconds
        has passed (prevents menus that are not accounted for after
        game end).
        """
        print(f"{interaction.user} pressed {button.label}!")
        view = UnoCardButtons(self.manager, len(self.manager.get_player_hand(0)))
        await interaction.response.send_message("Your cards:", view = view, ephemeral = True,
                                                delete_after = 60)
        # wait for the view to call self.stop() before we move beyond this point
        await view.wait()
        # delete the response to the card button press (the UnoCardButtons UI message)
        await interaction.delete_original_response()    
    
    @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Quit the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # remove current players from active player list
        # self.manager.remove_player(interaction)
        # if nobody else is left, then quit the game
        #if self.game.players == 0:
        #    await self.manager.quit_game(interaction)
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
        elif self.value == "": self.priority += 0
        else: self.priority += int(self.value)
    
    def __eq__(self, other):
        if not isinstance(other, Card): return False
        if self.name != other.name: return False
        if self.value != other.value: return False
        return True
    
    def __lt__(self, other):
        return self.priority < other.priority

    def __gt__(self, other):
        return self.priority > other.priority
    
    
def generate_deck_Uno():
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
        deck.append(UnoCard("Wild", ""))
        deck.append(UnoCard("Wild", "Draw Four"))
    return deck

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.skipped = False
        
    def get_playable_cards(self, top_card):
        playable_cards = [card for card in self.hand if card.color == top_card.color or card.value == top_card.value or card.color == "Wild"]
        return playable_cards