import discord
import games.counter

# Basic game class. No reason not to reference member vars directly
class BaseGame():
    def __init__(self, game_type=0, number_of_players=0, max_players=0, player_list=None, game_state=0):
        self.game_type = game_type
        self.number_of_players = number_of_players
        self.player_list = player_list
        self.game_state = game_state
        self.max_players = max_players


# TODO: Make this an actual abstract class
class GameManager():
    def __init__(self):
        self.game = BaseGame()
        self.base_gui = None


# General game factory class, handles interactions between the client and the game presenters
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

        await new_game.start_game(interaction)


    def stop_game(self, game):
        self.active_games.pop(game.channel_id)

