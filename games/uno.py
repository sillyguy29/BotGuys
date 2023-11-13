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
        #self.game.player_list.append(user_id)

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
            self.add_item(CardButton(self.manager, f"Green {i}"))
 
        
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
        view = UnoCardButtons(self.manager, 3)
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

