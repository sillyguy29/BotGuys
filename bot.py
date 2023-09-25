import discord
import responses
import sys



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