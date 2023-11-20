"""Bot fontend and setup

Contains everything that the bot uses at the frontend, including slash
commands, and starts up the bot.
"""
import discord
import cmd_control
from configs import config
from games import gamefactory
import logging
import datetime


# Inherit the discord client class so we can override some methods
class LanternClient(discord.Client):
    """
    Inhereted client class, needed to override setup_hook
    """
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.game_factory = gamefactory.GameFactory()


    async def setup_hook(self):
        """
        Called after the bot is logged in but before it is connected to 
        websocket.
        """
        await cmd_control.command_control(self.tree)


def create_commands(client):
    """
    Initiates all slash commands
    """
    @client.tree.command(name="hithere",
                            description="Testing slash command")
    async def test_slash_command(interaction: discord.Interaction):
        print(f"{interaction.user} used a slash command!")
        await interaction.response.send_message("Secret message", ephemeral=True)

    @client.tree.command(name="help", description="Learn about Lantern and its games")
    async def help_command(interaction: discord.Interaction):
        print(f"{interaction.user} used the help command!")
        await interaction.response.send_message("Check your DMs!", ephemeral=True)
        await interaction.user.send(config.HELP_MESSAGE)

    @client.tree.command(name="counter", description="Play a simple counter game")
    async def play_counter(interaction: discord.Interaction):
        print(f"{interaction.user} is starting a game!")
        await client.game_factory.start_game(interaction, game_type=0)

    @client.tree.command(name="blackjack", description="Play a game of Blackjack")
    @discord.app_commands.describe(
        cpus="Amount of cpu players (max of 3)"
    )
    async def play_blackjack(interaction: discord.Interaction, cpus: int):
        print(f"{interaction.user} is starting a game with {cpus} computer players!")
        await client.game_factory.start_game(interaction, game_type=1, cpus=cpus)

    @client.tree.command(name="uno", description="Play a game of Uno")
    @discord.app_commands.describe(
        cpus="Amount of cpu players (max of 3)"
    )
    async def play_uno(interaction: discord.Interaction, players: int, cpus: int):
        print(f"{interaction.user} is starting a game with {cpus} computer players!")
        await client.game_factory.start_game(interaction, game_type=3, cpus=cpus)

    @client.tree.command(name="getdebugdata", description="Get internal data for one or all games")
    @discord.app_commands.describe(
        channel_id=("The ID of the channel with an active game to get the"
                    " data from, leave blank to get all game data"),
        print_type=("Number indicating where to send the results."
                    " 1: print results here, 2: print results "
                    "in terminal, 3: write to file (default=2)")
    )
    async def get_debug(interaction: discord.Interaction, channel_id: int = None,
                         print_type: int = 2):
        await client.game_factory.get_debug_str(interaction, channel_id, print_type)


def run_bot(file_handler, cmd_loglevel):
    """
    Called by main, starts the bot
    """
    intents = discord.Intents.default()
    intents.message_content = True
    client = LanternClient(intents=intents)
    create_commands(client)

    @client.event
    async def on_ready():
        print(f"{client.user} is now running!")

    # command-line logger
    discord.utils.setup_logging(level=cmd_loglevel)
    client.run(config.TOKEN, log_handler=file_handler)
