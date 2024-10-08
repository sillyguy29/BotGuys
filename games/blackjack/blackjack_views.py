"""
Contains all views for blackjack
"""
import discord
from util import send_info_message


class QuitGameButton(discord.ui.View):
    """
    Button set that asks players if they want to play the game again
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "Go Again!", style = discord.ButtonStyle.green)
    async def restart(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Start a new round
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # stop accepting input
        self.stop()
        await self.manager.start_new_round(interaction)

    @discord.ui.button(label = "End Game", style = discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Quit the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # stop eccepting input
        self.stop()
        await interaction.channel.send(f"{interaction.user.mention} ended the game!")
        await self.manager.quit_game(interaction)


class BlackjackButtonsBase(discord.ui.View):
    """
    Initial "join game" buttons
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "Join", style = discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Lets the player join the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")

        await self.manager.add_player(interaction)

    @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Quit the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # remove current players from active player list
        await self.manager.remove_player(interaction)

    @discord.ui.button(label = "Start Game", style = discord.ButtonStyle.blurple)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Start the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # start the game
        await self.manager.start_game(interaction)


class BlackjackButtonsBaseGame(discord.ui.View):
    """
    Literally just a resend button
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "Resend", style = discord.ButtonStyle.gray)
    async def resend(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Resend base menu message
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # resend
        await self.manager.resend(interaction)


class BetModal(discord.ui.Modal):
    """
    Contains the popup box that shows when players make their bets
    """
    def __init__(self, manager):
        super().__init__(title="Bet")
        self.manager = manager

    # apparently you just kind of put this down and it works
    bet_box = discord.ui.TextInput(label="How much do you want to bet?",
                                   max_length=4,
                                   placeholder="Enter bet here...")

    async def on_submit(self, interaction: discord.Interaction):
        """
        Overriden method that activates when the user submits the form.
        """
        # converts the user's response into a string
        user_response = str(self.bet_box)
        # make sure the bet is valid
        if not user_response.isdigit():
            print(f"{interaction.user} failed to bet with response {user_response}")
            await send_info_message(f"{user_response} is not a valid number.", interaction)
            return
        print(f"{interaction.user} bet {user_response} chips.")
        await self.manager.make_bet(interaction, user_response)


class ButtonsBetPhase(discord.ui.View):
    """
    Contains the "bet" button and also keeps track of players who have
    placed bets
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "Bet!", style = discord.ButtonStyle.green)
    async def bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Allows the user to bring up the betting menu
        """
        print(f"{interaction.user} pressed {button.label}!")
        if not await self.manager.deny_non_participants(interaction):
            return
        await interaction.response.send_modal(BetModal(self.manager))


class HitOrStand(discord.ui.View):
    """
    Contains the "hit" and "stand" buttons when it's a certain player's
    turn. Keeps track of which player's turn it is and denies input
    to other players
    """
    def __init__(self, manager, active_player):
        super().__init__()
        self.manager = manager
        self.active_player = active_player
        self.disabled_view = None

    @discord.ui.button(label = "Hit Me!", style = discord.ButtonStyle.green)
    async def hit_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Check if the interaction is valid, and if so, call hit_user
        """
        print(f"{interaction.user} pressed {button.label}!")
        if interaction.user != self.active_player:
            await send_info_message("It's not your turn.", interaction)
            return
        # stop accepting interactions for this message
        self.stop()
        await self.manager.hit_user(interaction)

    @discord.ui.button(label = "Stand", style = discord.ButtonStyle.blurple)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Check if the interaction is valid, and if so, make the user stand
        and start the next player's turn
        """
        if interaction.user != self.active_player:
            await send_info_message("It's not your turn.", interaction)
            return
        print(f"{interaction.user} pressed {button.label}!")
        await interaction.response.send_message(f"{self.active_player.display_name} is standing!")
        # stop accepting interactions for this message
        self.stop()
        await self.manager.start_next_player_turn()
