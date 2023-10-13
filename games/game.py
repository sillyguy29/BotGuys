import discord
import games.counter

# Basic game class. No reason not to reference member vars directly
class BaseGame():
    def __init__(self, game_type=0, number_of_players=0, max_players=0, 
                 player_list=None, game_state=0, channel_id=None):
        self.game_type = game_type
        self.number_of_players = number_of_players
        self.player_list = player_list
        self.game_state = game_state
        self.max_players = max_players


# Base class for a game. Most of the methods should be overriden
class GameManager():
    def __init__(self, game, base_gui, channel_id, factory, current_active_menu):
        self.game = game
        self.base_gui = base_gui
        self.channel_id = channel_id
        self.factory = factory
        self.current_active_menu = current_active_menu

    async def create_game(self, interaction):
        await interaction.response.send_message(content=self.get_base_menu_string(), 
                                                view=self.base_gui)
        self.current_active_menu = await interaction.original_response()

    async def refresh(self):
        await self.current_active_menu.edit(content=self.get_base_menu_string(), 
                                            view=self.base_gui)

    async def resend(self):
        await self.current_active_menu.edit(view=None)
        # InteractionMessage inherits from Message so we can access the channel attribute
        self.current_active_menu = await self.current_active_menu.channel.send(
                                        self.get_base_menu_string(), view=self.base_gui)
        
    async def quit_game(self):
        await self.current_active_menu.edit(view=None)
        await self.factory.stop_game(self.channel_id)

    def get_base_menu_string(self):
        return "Generic game menu message"


# General game factory class, handles interactions between the client and the game presenters,
# manages all active games
class GameFactory():
    def __init__(self):
        self.active_games = dict()

    async def start_game(self, interaction, game_type):
        if interaction.channel_id in self.active_games:
            await interaction.response.send_message(content="A game has already" 
                                                    + "been started in this channel.",
                                                    ephemeral = True)
        
        if game_type == 0:
            new_game = games.counter.CounterManager(self, interaction.channel_id)
            self.active_games[interaction.channel_id] = new_game

        await new_game.create_game(interaction)

    async def stop_game(self, channel_id):
        self.active_games.pop(channel_id)
        

