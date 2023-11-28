"""Contains the factory that manages all active games.
"""
import logging
import datetime
from games.counter import CounterManager
from games.blackjack import BlackjackManager
from games.poker import PokerManager
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
            logging.info("Failed game creation due to existing active game in channel: [%i]",
                         interaction.channel_id)
            await interaction.response.send_message(content="A game has already"
                                                    + " been started in this channel.",
                                                    ephemeral = True)

        if game_type == 0:
            logging.info("New counter game created in channel: [%i]", interaction.channel_id)
            new_game = CounterManager(self, interaction.channel)
            self.active_games[interaction.channel_id] = new_game
            await new_game.create_game(interaction)

        elif game_type == 1:
            logging.info("New blackjack game created in channel: [%i]", interaction.channel_id)
            new_game = BlackjackManager(self, interaction.channel)
            self.active_games[interaction.channel_id] = new_game
            await new_game.create_game(interaction)

        elif game_type == 2:
            logging.info("New poker game created in channel: [%i]", interaction.channel_id)
            new_game = PokerManager(self, interaction.channel, cpus)
            self.active_games[interaction.channel_id] = new_game
            await new_game.create_game(interaction)

        elif game_type == 3:
            logging.info("New uno game created in channel: [%i]", interaction.channel_id)
            new_game = UnoManager(self, interaction.channel, interaction.user)
            self.active_games[interaction.channel_id] = new_game
            await new_game.create_game(interaction)

        else:
            logging.error("Error: unknown game type creation attempted in channel [%i]",
                          interaction.channel_id)
            raise ValueError("Unrecognized game type")


    async def stop_game(self, channel_id):
        """
        Removes a game from the managed games dictionary. This should
        be called by a game that stops, however it does not stop
        everything by itself. All active menus must be shut down
        in order to actually stop a game.
        """
        logging.info("[%i] Game stopping.", channel_id)
        self.active_games.pop(channel_id)

    async def get_debug_str(self, interaction, channel_id, print_type):
        """
        Retrieves internal data for one or all games.

        channel_id -> channel to get data from, if None gets data for
        all channels
        print_type -> 1: In discord, 2: In terminal, 3: In file
        """
        debug_str = f"DEBUG DATA\nRetrieved {datetime.datetime.now(datetime.timezone.utc)}\n"
        if channel_id is None:
            logging.info("Debug data for all channels requested")
            for (k,v) in self.active_games.items():
                debug_str += (f"CHANNEL ID: {k} AT "
                              f"{datetime.datetime.now(datetime.timezone.utc)}\n\n")
                debug_str += v.get_debug_str()
        else:
            logging.info("Debug data for channel %i requested", channel_id)
            if channel_id not in self.active_games:
                logging.info("No game in channel, not returning debug")
                await send_info_message("There is no game currently in this channel.", interaction)
                return
            debug_str += (f"CHANNEL ID: {channel_id} "
                          f"AT {datetime.datetime.now(datetime.timezone.utc)}\n\n")
            debug_str += self.active_games[channel_id].get_debug_str()

        if print_type == 1:
            await interaction.response.send_message(debug_str)
            logging.info("Debug data sent to discord")
        elif print_type == 2:
            await send_info_message("Retrieved debug string, printing in terminal.", interaction)
            print(debug_str)
            logging.info("Debug data sent to terminal")
        elif print_type == 3:
            date = str(datetime.datetime.now(datetime.timezone.utc)).replace(":", " ")
            fname = f"logs/DEBUG_{date}.txt"
            with open(fname, "w", encoding="utf-8") as file:
                file.write(debug_str)
            await send_info_message(f"Retrieved debug string, saved to file {fname}.",
                                    interaction)
            logging.info("Debug data saved to file %s", fname)
