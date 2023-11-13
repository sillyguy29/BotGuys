import discord
from games.game import BaseGame
from games.game import GameManager
from util import Card
from util import generate_deck_Uno
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
      
        
class UnoManager(GameManager):
    def __init__(self, factory, channel_id, user_id):
        super().__init__(UnoGame(), UnoButtonsBase(self),
                         channel_id, factory)
        
        # What is player_list? We have player_data (dict) in the game model
        self.game.player_list.append(user_id)

    async def create_game(self, interaction):
        raise NotImplementedError("Override this method based on uno specifications")
    
    async def start_game(self, interaction):
        # game_state == 4 -> players cannot join or leave
        self.game.game_state = 4
        await self.gameplay_loop()
        
    def get_base_menu_string(self):
        if self.game.game_state == 1:
            return "Welcome to this game of Uno. Feel free to join."
        elif self.game.game_state == 4:
            return "Game has started!"

        
class UnoButtonsBase(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager