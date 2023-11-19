# Initialize important global variables
with open("configs/bot_token.txt", "r") as token_file:
    global TOKEN
    TOKEN = token_file.read()

with open("configs/guild_id.txt", "r") as id_file:
    global GUILD_ID
    GUILD_ID = int(id_file.read())

with open('help_info.txt', 'r') as help_file:
    global HELP_MESSAGE
    HELP_MESSAGE = help_file.read()
