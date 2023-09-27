import discord
import responses
from discord.ext import commands
import sys

global GUILD_ID
id_file = open("guild_id.txt", "r")
GUILD_ID = int(id_file.read())
id_file.close()

class BlackjackButtons(discord.ui.View):
    def __init__(self):
        super().__init__()
        #self.label = label
        #self.add_item(discord.ui.Button(label = self.label))

    @discord.ui.button(label = "Hit Me!", style = discord.ButtonStyle.green)
    async def hit_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You've been hit by", ephemeral = True)


async def send_message(message, user_message, is_private):
    try:
        response = responses.handle_responses(user_message)
        if is_private:
            await message.author.send(response)
        else:
            await message.channel.send(response)
    except Exception as e:
        print(e)

def create_commands(command_tree):
    @command_tree.command(name="hithere", 
                          description="Testing slash command")
    async def test_slash_command(interaction: discord.Interaction):
        print("{} used a slash command!".format(interaction.user))
        await interaction.response.send_message("Secret message", ephemeral=True)

    @command_tree.command(name = "blackjack", 
                          description = "Start a new game of Blackjack", guild=discord.Object(id=GUILD_ID))
    async def start_blackjack(interaction: discord.Interaction):
        print("Someone started a game of Blackjack")
        view = BlackjackButtons()
        await interaction.response.send_message("Blackjack stuff", view=view, ephemeral=True)

def run_bot():
    token_file = open("bot_token.txt", "r")
    TOKEN = token_file.read()
    token_file.close()


    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    command_tree = discord.app_commands.CommandTree(client)
    create_commands(command_tree)

    @client.event
    async def on_ready():
        await command_tree.sync(guild=discord.Object(id=GUILD_ID))
        print("{} is now running".format(client.user))

    @client.event
    async def on_message(message):
        if message.author == client.user: #Prevents bot from responding to its own messages
            return
        username = str(message.author)
        user_message = str(message.content)
        channel = str(message.channel)
        print("{0} said {1} in {2}".format(username, user_message, channel))

        if user_message[0] == '?':
            user_message = user_message[1:] #Removes the '?' message start
            await send_message(message, user_message, is_private=True)
        else:
            user_message = user_message[1:] #Removes the '!' message start
            await send_message(message, user_message, is_private=False)

    client.run(TOKEN)