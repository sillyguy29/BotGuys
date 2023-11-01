"""Contains the factory that manages all active games.
"""
from games.counter import CounterManager
from games.blackjack import BlackjackManager


class GameFactory():
    """
    General game factory class, handles interactions between the client and the game presenters,
    manages all active games. This class should not use any mutator methods in the manager classes
    except for create_game.
    """
    def __init__(self):
        self.active_games = {}

    async def start_game(self, interaction, game_type, players=0, cpus=0):
        """
        Starts a game specified by the ID of game_type.

        ID Key:
        ----
        0 = Counter
        1 = Blackjack
        """
        if interaction.channel_id in self.active_games:
            await interaction.response.send_message(content="A game has already"
                                                    + " been started in this channel.",
                                                    ephemeral = True)

        if game_type == 0:
            new_game = CounterManager(self, interaction.channel_id)
            self.active_games[interaction.channel_id] = new_game
            await new_game.create_game(interaction)

        if game_type == 1:
            new_game = BlackjackManager(self, interaction.channel_id, interaction.user,
                                         players, cpus)
            self.active_games[interaction.channel_id] = new_game
            await new_game.create_game(interaction)

        else:
            raise ValueError("Unrecognized game type")

        await new_game.create_game(interaction)


    async def stop_game(self, channel_id):
        """
        Removes a game from the managed games dictionary. This should
        be called by a game that stops, however it does not stop
        everything by itself. All active menus must be shut down
        in order to actually stop a game.
        """
        self.active_games.pop(channel_id)
