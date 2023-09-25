import discord
import responses

async def send_message(message, userMessage, isPrivate):
    try:
        response = responses.handle_responses(userMessage)
        if isPrivate:
            await message.author.send(response)
        else:
            await message.channel.send(response)
    except Exception as e:
        print(e)

def runBot():
    tokenFile = open("bot_token.txt", "r")
    TOKEN = tokenFile.read()
    tokenFile.close()

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print("{} is now running".format(client.user))

    @client.event
    async def on_message(message):
        if message.author == client.user: #Prevents bot from responding to its own messages
            return
        username = str(message.author)
        userMessage = str(message.content)
        channel = str(message.channel)
        print("{0} said {1} in {2}".format(username, userMessage, channel))

        if userMessage[0] == '?':
            userMessage = userMessage[1:] #Removes the '?' message start
            await send_message(message, userMessage, isPrivate=True)
        else:
            userMessage = userMessage[1:] #Removes the '!' message start
            await send_message(message, userMessage, isPrivate=False)

    client.run(TOKEN)