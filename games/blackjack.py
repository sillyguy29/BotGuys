"""Blackjack game module

Contains all the logic needed to run a game of Blackjack.
It features an closed game model, meaning not all users can interact
with the game at any time, and there is player management.
"""
import discord
from games.game import BaseGame
from games.game import GameManager
from util import Card
from util import generate_deck
import random


class BlackjackGame(BaseGame):
    """
    Blackjack game model class. Keeps track of the deck and none else
    """
    def __init__(self):
        super().__init__(game_type=1)
        
        self.deck = generate_deck()
        random.shuffle(self.deck)
        
        self.players_list = []
 
        
class BlackjackManager(GameManager):
    def __init__(self, factory, channel_id, user_id, players, cpus):
        super().__init__(BlackjackGame(), BlackjackButtonsBase(self), channel_id, factory, user_id, players, cpus)
        
        self.game.players_list.append(user_id)
        
    def get_base_menu_string(self):
        return "Welcome to this game of Blackjack. Feel free to join."
    
    async def add_player(self, interaction):
        """
        Adds the players who joined to the players list
        """
        # check to make sure the game hasn't ended, do nothing if it has
        if await self.game_end_check(interaction):
            return
        
        if len(self.game.players_list) < 6 and interaction.user not in self.game.players_list:
            print(interaction.user + "was added to the players list!")
            await interaction.response.send_message("You joined!", ephemeral = True)
            self.game.players_list.append(interaction.user)
            await self.factory.add_player(interaction.user)
        else:
            await interaction.response.send_message("You were unable to join!", ephemeral = True)
            return
        
        # resend the base menu with the updated game state
        await self.resend(interaction)
        
    async def remove_all_players(self):
        """
        Removes all players from the players list
        """
        await self.factory.remove_players(self.game.players_list)

     
class BlackjackButtonsBase(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
    
    @discord.ui.button(label = "Join", style = discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Send an ephemeral message to the person who interacted with
        this button that contains the hit or miss menu. This menu
        will be deleted after it is interacted with or 60 seconds
        has passed (prevents menus that are not accounted for after
        game end).
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # attempt to add player to the game
        await self.manager.add_player(interaction)
    
    @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Quit the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # remove current players from active player list
        self.manager.remove_all_players
        # ask our manager to quit this game
        await self.manager.quit_game(interaction)
        
        
def bj_add(cards):
    """
    cards is a list of Card objects
    returns an integer corresponding to the value of the hand in
    a game of blackjack
    """
    total = 0
    ace_count = 0
    faces = ('A', 'J', 'Q', 'K')
    for card in cards:
        if card.face not in faces:
            total += int(card.face)
        elif card.face in faces[1:]:
            total += 10
        else:
            ace_count += 1
    total += 11 * ace_count
    for ace in range(ace_count):
        if total > 21:
            total -= 10
    return total

def play_bj(deck, action):
    """
    Simulates a player playing Blackjack.
    deck is the current game's deck
    action is the player's action
    """
    hand_visible = []
    hand_flipped = []
    bust = False
    while hand_visible.count < 2:
        c = deck[random.randint(0, deck.count - 1)]
        hand_visible.add(c)
        deck.remove(c)
    
    while not bust:
        if action == "Hit":
            c = deck[random.randint(0, deck.count - 1)]
            hand_visible.add(c)
            deck.remove(c)
            if bj_add(hand_visible) > 21:
                bust = True
            continue
        
        if action == "Double Down" and bj_add(hand_visible) in range(9, 12):
            # Doubles bet
            c = deck[random.randint(0, deck.count - 1)]
            hand_flipped.add(c)
            deck.remove(c)
            break
        
        if action == "Stand":
            break