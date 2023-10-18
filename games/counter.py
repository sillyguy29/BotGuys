import discord
from games.game import BaseGame
from games.game import GameManager


class CounterGame(BaseGame):
    def __init__(self):
        super().__init__(game_type=0)
        self.count = 0


# TODO: Handle cases where a user closes a game and another user attempts
# to interact with the closed game, might cause issues
class CounterManager(GameManager):
    def __init__(self, factory, channel_id):
        super().__init__(CounterGame(), CounterButtonsBase(self), channel_id, factory, None)

    def get_base_menu_string(self):
        return "Counter: {}".format(self.game.count)
    
    async def increment(self):
        self.game.count += 1
        await self.resend()

    async def decrement(self):
        self.game.count -= 1
        await self.resend()


class HitOrMiss(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    @discord.ui.button(label = "Hit Me!", style = discord.ButtonStyle.green)
    async def hit_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await self.manager.increment()
        await interaction.response.send_message("You've hit it!", ephemeral = True)

    @discord.ui.button(label = "Miss Me!", style = discord.ButtonStyle.green)
    async def miss_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await self.manager.decrement()
        await interaction.response.send_message("You've missed it!", ephemeral = True)
    

class CounterButtonsBase(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
    
    @discord.ui.button(label = "Hit or Miss", style = discord.ButtonStyle.green)
    async def hit_miss(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = HitOrMiss(self.manager)
        await interaction.response.send_message("Hit or Miss?", view = view, ephemeral = True)
        await view.wait()
        await interaction.delete_original_response()

    @discord.ui.button(label = "Refresh", style = discord.ButtonStyle.blurple)
    async def ref(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.manager.refresh()
        await interaction.response.send_message("Refreshing the counter...", ephemeral = True)

    @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.manager.quit_game()



    

