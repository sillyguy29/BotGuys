"""
Quick startup that bypasses command sync menu
"""
import sys
from bot import create_commands, get_loglevel
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
    def __init__(self, *, intents: discord.Intents,
                 cmd_handler=logging.INFO, file_handler=logging.INFO):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.game_factory = gamefactory.GameFactory()
        self.cmd_handler = cmd_handler
        self.file_handler = file_handler


if __name__ == "__main__":
    args = sys.argv
    if len(args) >= 3:
        file_loglevel = args[2].lower().strip()
        if file_loglevel not in ("critical", "error", "warning", "info", "debug"):
            print("Unknown file logging level.")
            sys.exit()
        file_loglevel = get_loglevel(file_loglevel)
    else:
        file_loglevel = logging.INFO

    if len(args) >= 2:
        cmd_loglevel = args[1].lower().strip()
        if cmd_loglevel not in ("critical", "error", "warning", "info", "debug"):
            print("Unknown cmd logging level.")
            sys.exit()
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
