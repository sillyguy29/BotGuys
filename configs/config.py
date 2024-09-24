"""Configs file that the bot will pull from.
"""
with open("configs/bot_token.txt", mode="r", encoding="utf-8") as token_file:
    global TOKEN
    TOKEN = token_file.read()

with open("configs/guild_id.txt", mode="r", encoding="utf-8") as id_file:
    global GUILD_ID
    GUILD_ID = int(id_file.read())

with open("configs/help_info.md", mode="r", encoding="utf-8") as help_file:
    global HELP_MESSAGE
    HELP_MESSAGE = help_file.read()
