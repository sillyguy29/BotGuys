import discord
from games.game import BaseGame
from games.game import GameManager


class CounterGame(BaseGame):
    def __init__(self):
        super().__init__(game_type=0)
        self.count = 0


# TODO: Handle cases where a user closes a game and another user attempts
# to interact with the closed game
class CounterManager(GameManager):
    def __init__(self, factory, channel_id):
        self.game = CounterGame()
        self.base_gui = CounterButtonsBase(self)
        self.factory = factory
        self.channel_id = channel_id

    async def start_game(self, interaction):
        await interaction.response.send_message("Counter: 0", view=self.base_gui)

    async def refresh_resend(self, interaction):
        self.base_gui.clear_items()
        self.base_gui = CounterButtonsBase(self)
        await interaction.response.send_message("Counter: {}".format(self.game.count),
                                                 view=self.base_gui)
        
    async def quit_game(self):
        self.base_gui.clear_items()
        self.base_gui.stop()
        self.factory.stop_game(self)

    def get_count(self, interaction):
        return self.game.count
    
    def increment(self, interaction):
        self.game.count += 1
        self.refresh_resend(interaction)

    def decrement(self, interaction):
        self.game.count -= 1
        self.refresh_resend(interaction)


class HitOrMiss(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    @discord.ui.button(label = "Hit Me!", style = discord.ButtonStyle.green)
    async def hit_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.manager.increment(interaction)
        await interaction.response.send_message("You've hit it!", ephemeral = True)

    @discord.ui.button(label = "Miss Me!", style = discord.ButtonStyle.green)
    async def miss_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.manager.decrement(interaction)
        await interaction.response.send_message("You've missed it!", ephemeral = True)
    

class CounterButtonsBase(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
    
    @discord.ui.button(label = "Hit or Miss", style = discord.ButtonStyle.green)
    async def hit_miss(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = HitOrMiss(self.manager)
        await interaction.response.send_message("Hit or Miss?", view = view, ephemeral = True)

    @discord.ui.button(label = "Refresh", style = discord.ButtonStyle.blurple)
    async def un_hit_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.manager.refresh_resend(interaction)

    @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.manager.quit_game()



    

