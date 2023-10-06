import discord
import responses
import sys
import cmd_control
import logging
import config

counter = 0

# Inherit the discord client class so we can override some methods
class LanternClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        await cmd_control.command_control(self.tree)


class BlackjackButtons(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label = "Hit Me!", style = discord.ButtonStyle.green, custom_id="hit me")
    async def hit_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        global counter
        counter += 1
        await interaction.response.send_message("You've been hit by: {}".format(counter), ephemeral = True)
    
    @discord.ui.button(label = "Pass!", style = discord.ButtonStyle.red)
    async def pass_turn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Gets the custom_id of the "Hit Me!" button and disables it when this button is clicked
        hitme_button = [x for x in self.children if x.custom_id=="hit me"][0]
        hitme_button.disabled = True
        # Changes the text on "Pass!" button to "Passed!" and disables the button
        button.label = "Passed!"
        button.disabled = True
        await interaction.response.edit_message(view=self)


async def send_message(message, user_message, is_private):
    try:
        response = responses.handle_responses(user_message)
        if is_private:
            await message.author.send(response)
        else:
            await message.channel.send(response)
    except Exception as e:
        print(e)
            
def create_commands(client):
    @client.tree.command(name="hithere", 
                            description="Testing slash command")
    async def test_slash_command(interaction: discord.Interaction):
        print("{} used a slash command!".format(interaction.user))
        await interaction.response.send_message("Secret message", ephemeral=True)

    @client.tree.command(name = "blackjack", 
                          description = "Start a new game of Blackjack")
    async def start_blackjack(interaction: discord.Interaction):
        print("Someone started a game of Blackjack")
        view = BlackjackButtons()
        await interaction.response.send_message("Blackjack stuff", view=view, ephemeral=True)


#TODO: Refactor this function and remove unnecessary code
def run_bot():
    global counter
    counter = 0
    intents = discord.Intents.default()
    intents.message_content = True
    client = LanternClient(intents=intents)
    create_commands(client)

    @client.event
    async def on_ready():
        print("{} is now running".format(client.user))

    @client.event
    async def on_ready():
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


    discord.utils.setup_logging(level=logging.INFO)


    client.run(config.TOKEN)