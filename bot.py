"""Bot fontend and setup

Contains everything that the bot uses at the frontend, including slash
commands, and starts up the bot.
"""
import logging
import datetime
import discord
import cmd_control
from configs import config
from games import gamefactory


# Inherit the discord client class so we can override some methods
class LanternClient(discord.Client):
    """
    Inhereted client class, needed to override setup_hook
    """
    def __init__(self, *, intents: discord.Intents,
                 cmd_handler=logging.INFO, file_handler=logging.INFO):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.game_factory = gamefactory.GameFactory()
        self.cmd_handler = cmd_handler
        self.file_handler = file_handler


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
        logging.info("Hithere slash command used in channel [%i]", interaction.channel_id)
        await interaction.response.send_message("Secret message", ephemeral=True)

    @client.tree.command(name="help", description="Learn about Lantern and its games")
    async def help_command(interaction: discord.Interaction):
        logging.info("Help slash command used in channel [%i]", interaction.channel_id)
        await interaction.response.send_message("Check your DMs!", ephemeral=True)
        await interaction.user.send(config.HELP_MESSAGE)

    @client.tree.command(name="counter", description="Play a simple counter game")
    async def play_counter(interaction: discord.Interaction):
        logging.info("Counter slash command used in channel [%i]", interaction.channel_id)
        await client.game_factory.start_game(interaction, game_type=0)

    @client.tree.command(name="blackjack", description="Play a game of Blackjack")
    async def play_blackjack(interaction: discord.Interaction):
        logging.info("Blackjack slash command used in channel [%i]", interaction.channel_id)
        await client.game_factory.start_game(interaction, game_type=1)

    @client.tree.command(name="poker", description="Play a game of Poker")
    @discord.app_commands.describe(
        cpus="Amount of cpu players (max of 3)"
    )
    async def play_poker(interaction: discord.Interaction, cpus: int):
        logging.info("Poker slash command used in channel [%i]", interaction.channel_id)
        await client.game_factory.start_game(interaction, game_type=2, cpus=cpus)

    @client.tree.command(name="uno", description="Play a game of Uno")
    async def play_uno(interaction: discord.Interaction):
        logging.info("Uno slash command used in channel [%i]", interaction.channel_id)
        await client.game_factory.start_game(interaction, game_type=3)

    @client.tree.command(name="getdebugdata", description="Get internal data for one or all games")
    @discord.app_commands.describe(
        channel_id=("The ID of the channel with an active game to get the"
                    " data from, leave blank to get all game data"),
        print_type=("Number indicating where to send the results."
                    " 1: send here, 2: terminal, 3: debug file (default=2)")
    )
    async def get_debug(interaction: discord.Interaction, channel_id: int = None,
                         print_type: int = 2):
        logging.info("Debug slash command used in channel [%i]", interaction.channel_id)
        await client.game_factory.get_debug_str(interaction, channel_id, print_type)

    @client.tree.command(name="setloglevel", description="Set the level of the specified logger")
    @discord.app_commands.describe(
        logger_type="0(default): root, 1: discord, 2: asyncio",
        log_level="0(default): NOTSET, 10: DEBUG, 20: INFO, 30: WARNING, 40: ERROR, 50: CRITICAL"
    )
    async def set_logger_level(interaction: discord.Interaction, logger_type: int = 0,
                            log_level: int = 0):
        if log_level > 50 or log_level < 0 or log_level % 10 != 0:
            await interaction.response.send_message("Invalid log level.")
            return
        if logger_type == 1:
            log = logging.getLogger("asyncio")
        elif logger_type == 2:
            log = logging.getLogger("discord")
        else:
            log = logging.getLogger()
        log.setLevel(log_level)
        log.critical("Log level changed to %i", log_level)
        await interaction.response.send_message("Log level changed.")

    @client.tree.command(name="sethandlerlevel",
                         description="Set the level of the specified log handler")
    @discord.app_commands.describe(
        handler_type="0: file, 1: terminal",
        log_level="0(default): NOTSET, 10: DEBUG, 20: INFO, 30: WARNING, 40: ERROR, 50: CRITICAL"
    )
    async def set_handler_level(interaction: discord.Interaction, handler_type: int,
                            log_level: int = 0):
        if log_level > 50 or log_level < 0 or log_level % 10 != 0:
            await interaction.response.send_message("Invalid log level.")
            return
        if handler_type == 0:
            handler = client.file_handler
        elif handler_type == 1:
            handler = client.cmd_handler
        handler.setLevel(log_level)
        r = {"msg": f"Log level changed to {log_level}"}
        record = logging.makeLogRecord(r)
        record.levelno = 50
        record.levelname = "CRITICAL"
        handler.emit(record)
        await interaction.response.send_message("Log level changed.")


def get_loglevel(level_str):
    # there has to be a better way to do this but I don't know it
    if level_str == "critical":
        return logging.CRITICAL
    elif level_str == "error":
        return logging.ERROR
    elif level_str == "warning":
        return logging.WARNING
    elif level_str == "info":
        return logging.INFO
    elif level_str == "debug":
        return logging.DEBUG


def run_bot(args):
    """
    Called by main, starts the bot
    """
    if len(args) >= 3:
        file_loglevel = args[2].lower().strip()
        if file_loglevel not in ("critical", "error", "warning", "info", "debug"):
            print("Unknown logging level.")
            return
        file_loglevel = get_loglevel(file_loglevel)
    else:
        file_loglevel = logging.INFO

    if len(args) >= 2:
        cmd_loglevel = args[1].lower().strip()
        if cmd_loglevel not in ("critical", "error", "warning", "info", "debug"):
            print("Unknown logging level.")
            return
        cmd_loglevel = get_loglevel(cmd_loglevel)
    else:
        cmd_loglevel = logging.INFO

    log = logging.getLogger()
    disc_log = logging.getLogger("discord")
    async_log = logging.getLogger("asyncio")

    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}',
                                  dt_fmt, style='{')

    date = str(datetime.datetime.now(datetime.timezone.utc)).replace(":", " ")
    fname = f"logs/LOG_{date}.txt"
    file_handler = logging.FileHandler(filename=fname, encoding="utf-8", mode="w")
    file_handler.setLevel(file_loglevel)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    cmd_handler = logging.StreamHandler()
    cmd_handler.setLevel(cmd_loglevel)
    cmd_handler.setFormatter(formatter)
    log.addHandler(cmd_handler)

    if cmd_loglevel == logging.DEBUG or file_loglevel == logging.DEBUG:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
    disc_log.setLevel(logging.INFO)
    async_log.setLevel(logging.WARNING)

    intents = discord.Intents.default()
    intents.message_content = True
    client = LanternClient(intents=intents, cmd_handler=cmd_handler, file_handler=file_handler)
    create_commands(client)

    @client.event
    async def on_ready():
        logging.info("%s is now running", client.user)

    client.run(token=config.TOKEN, log_handler=None)
