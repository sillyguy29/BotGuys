"""Contains the factory that manages all active games.
"""
import logging
import datetime
from games.counter import CounterManager
from games.blackjack import BlackjackManager
from games.uno import UnoManager
from util import send_info_message


class GameFactory():
    """
    General game factory class, handles interactions between the client and the game presenters,
    manages all active games. This class should not use any mutator methods in the manager classes
    except for create_game.
    """
    def __init__(self):
        self.active_games = {}

    async def start_game(self, interaction, game_type, cpus=0):
        """
        Starts a game specified by the ID of game_type.

        ID Key:
        ----
        0 = Counter
        1 = Blackjack
        2 = Poker
        3 = Uno
        4 = Love Letter
        """
        if interaction.channel_id in self.active_games:
            await interaction.response.send_message(content="A game has already"
                                                    + " been started in this channel.",
                                                    ephemeral = True)

        if game_type == 0:
            new_game = CounterManager(self, interaction.channel)
            self.active_games[interaction.channel_id] = new_game
            await new_game.create_game(interaction)

        elif game_type == 1:
            new_game = BlackjackManager(self, interaction.channel, cpus)
            self.active_games[interaction.channel_id] = new_game
            await new_game.create_game(interaction)

        elif game_type == 3:
            new_game = UnoManager(self, interaction.channel, interaction.user)
            self.active_games[interaction.channel_id] = new_game
            await new_game.create_game(interaction)

        else:
            raise ValueError("Unrecognized game type")


    async def stop_game(self, channel_id):
        """
        Removes a game from the managed games dictionary. This should
        be called by a game that stops, however it does not stop
        everything by itself. All active menus must be shut down
        in order to actually stop a game.
        """
        self.active_games.pop(channel_id)

    async def get_debug_str(self, interaction, channel_id, print_type):
        debug_str = f"DEBUG DATA\nRetrieved {datetime.datetime.now(datetime.timezone.utc)}\n"
        if channel_id is None:
            for (k,v) in self.active_games.items():
                debug_str += (f"CHANNEL ID: {k} AT "
                              f"{datetime.datetime.now(datetime.timezone.utc)}\n\n")
                debug_str += v.get_debug_str()
        else:
            if channel_id not in self.active_games:
                await send_info_message("There is no game currently in this channel.", interaction)
                return
            debug_str += (f"CHANNEL ID: {channel_id} "
                          f"AT {datetime.datetime.now(datetime.timezone.utc)}\n\n")
            debug_str += self.active_games[channel_id].get_debug_str()

        if print_type == 1:
            await interaction.response.send_message(debug_str)
        elif print_type == 2:
            await send_info_message("Retrieved debug string.", interaction)
            print(debug_str)
        elif print_type == 3:
            await send_info_message("Retrieved debug string.", interaction)
            date = str(datetime.datetime.now(datetime.timezone.utc)).replace(":", " ")
            fname = f"logs/DEBUG_{date}.txt"
            with open(fname, "w", encoding="utf-8") as file:
                file.write(debug_str)
