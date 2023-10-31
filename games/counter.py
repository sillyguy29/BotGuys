"""Counter game module

Contains all the logic needed to run the counter game. This game is
intended to serve as a reference to build other games and is very
basic. It features an open game model, meaning any user can interact
with the game at any time, and there is no player management.
"""
import discord
from games.game import BaseGame
from games.game import GameManager


class CounterGame(BaseGame):
    """
    Counter game model class. Keeps track of the counter and none else
    """
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
        super().__init__(CounterGame(), game=CounterButtonsBase(self), 
                         channel_id=channel_id, factory=factory)

    def get_base_menu_string(self):
        return f"Counter: {self.game.count}"

    async def increment(self, interaction):
        """
        Increment the counter and resend menu
        """
        # check to make sure the game hasn't ended, do nothing if it has
        if await self.game_end_check(interaction):
            return

        self.game.count += 1
        # send a secret message to the person who pressed this button. This message auto-deletes
        # after 10 seconds (doesn't need to be around for much longer)
        await interaction.response.send_message("You've hit it!", ephemeral = True,
                                                delete_after = 10)
        # resend the base menu with the updated game state
        await self.resend(interaction)

    async def decrement(self, interaction):
        """
        Decrement the counter and resend menu
        """
        # check to make sure the game hasn't ended, do nothing if it has
        if await self.game_end_check(interaction):
            return

        self.game.count -= 1
        # send a secret message to the person who pressed this button. This message auto-deletes
        # after 10 seconds (doesn't need to be around for much longer)
        await interaction.response.send_message("You've missed it!", ephemeral = True,
                                                delete_after = 10)
        # resend the base menu with the updated game state
        await self.resend(interaction)


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
        """
        Call increment
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # stop accepting interactions for this message
        self.stop()
        await self.manager.increment(interaction)

    @discord.ui.button(label = "Miss Me!", style = discord.ButtonStyle.red)
    async def miss_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Call decrement
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
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
        """
        Send an ephemeral message to the person who interacted with
        this button that contains the hit or miss menu. This menu
        will be deleted after it is interacted with or 60 seconds
        has passed (prevents menus that are not accounted for after
        game end).
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        view = HitOrMiss(self.manager)
        await interaction.response.send_message("Hit or Miss?", view = view, ephemeral = True,
                                                delete_after = 60)
        # wait for the view to call self.stop() before we move beyond this point
        await view.wait()
        # delete the response to the hit or miss button press (the HitOrMiss UI message)
        await interaction.delete_original_response()

    @discord.ui.button(label = "Refresh", style = discord.ButtonStyle.blurple)
    async def ref(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Edit the current active menu to accurately represent the
        current game state, do not send a new message.
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # get the manager of this view to refresh the base menu message
        await self.manager.refresh(interaction)
        # send a secret message to the person who pressed this button. This message auto-deletes
        # after 10 seconds (doesn't need to be around for much longer)
        await interaction.response.send_message("Refreshing the counter...", ephemeral = True,
                                                delete_after = 10)

    @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Quit the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # ask our manager to quit this game
        await self.manager.quit_game(interaction)
