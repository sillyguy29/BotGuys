import discord
from games.game import BaseGame
from games.game import GameManager


class CounterGame(BaseGame):
    def __init__(self):
        # game_type = 0 -> counter game
        super().__init__(game_type=0)
        # data specific to this game (counter) defined here
        self.count = 0


class CounterManager(GameManager):
    """
    Manages a counter game. Has operations to increment and decrement the count
    """
    def __init__(self, factory, channel_id):
        super().__init__(CounterGame(), CounterButtonsBase(self), channel_id, factory, None)

    def get_base_menu_string(self):
        return "Counter: {}".format(self.game.count)
    
    async def increment(self, interaction):
        # check to make sure the game hasn't ended, do nothing if it has
        if await self.game_end_check(interaction):
            return
        
        self.game.count += 1
        # send a secret message to the person who pressed this button. This message auto-deletes
        # after 10 seconds (doesn't need to be around for much longer)
        await interaction.response.send_message("You've hit it!", ephemeral = True,
                                                delete_after = 10)
        # resend the base menu with the updated game state
        await self.resend()

    async def decrement(self, interaction):
        # check to make sure the game hasn't ended, do nothing if it has
        if await self.game_end_check(interaction):
            return
        
        self.game.count -= 1
        # send a secret message to the person who pressed this button. This message auto-deletes
        # after 10 seconds (doesn't need to be around for much longer)
        await interaction.response.send_message("You've missed it!", ephemeral = True,
                                                delete_after = 10)
        # resend the base menu with the updated game state
        await self.resend()


class HitOrMiss(discord.ui.View):
    """
    Button group used on the private message that users use to increment and decrement
    the counter for the game.
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    @discord.ui.button(label = "Hit Me!", style = discord.ButtonStyle.green)
    async def hit_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        # stop accepting interactions for this message
        self.stop()
        await self.manager.increment(interaction)

    @discord.ui.button(label = "Miss Me!", style = discord.ButtonStyle.green)
    async def miss_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        # stop accepting interactions for this message
        self.stop()
        await self.manager.decrement(interaction)
    

class CounterButtonsBase(discord.ui.View):
    """
    Base menu button group for the counter game.
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
    
    @discord.ui.button(label = "Hit or Miss", style = discord.ButtonStyle.green)
    async def hit_miss(self, interaction: discord.Interaction, button: discord.ui.Button):
        # send a private message to the person who pressed this button with the hit or miss view,
        # it auto deletes after 60 seconds (prevents dangling messages that can force the game to 
        # stay in memory after it ends)
        view = HitOrMiss(self.manager)
        await interaction.response.send_message("Hit or Miss?", view = view, ephemeral = True,
                                                delete_after = 60)
        # wait for the view to call self.stop() before we move beyond this point
        await view.wait()
        # delete the response to the hit or miss button press (the HitOrMiss UI message)
        await interaction.delete_original_response()

    @discord.ui.button(label = "Refresh", style = discord.ButtonStyle.blurple)
    async def ref(self, interaction: discord.Interaction, button: discord.ui.Button):
        # get the manager of this view to refresh the base menu message
        await self.manager.refresh(interaction)
        # send a secret message to the person who pressed this button. This message auto-deletes
        # after 10 seconds (doesn't need to be around for much longer)
        await interaction.response.send_message("Refreshing the counter...", ephemeral = True,
                                                delete_after = 10)

    @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        # as our manager to quit this game
        await self.manager.quit_game(interaction)



    

