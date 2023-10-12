
# Initialize important global variables
token_file = open("configs/bot_token.txt", "r")
global TOKEN
TOKEN = token_file.read()
token_file.close()

id_file = open("configs/guild_id.txt", "r")
global GUILD_ID
GUILD_ID = int(id_file.read())
id_file.close()