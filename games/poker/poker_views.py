import discord
from util import send_info_message


class PokerButtonsBase(discord.ui.View):
    """
    Button set that asks players if they want to play the game again
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "Join", style = discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
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

        await self.manager.add_player(interaction)

    @discord.ui.button(label = "Add CPU", style = discord.ButtonStyle.blurple)
    async def add_cpu(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Adds a CPU player
        """
        await self.manager.add_cpu(0, interaction)

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


class PokerButtonsBaseGame(discord.ui.View):
    """
    Button set that asks players if they want to play the game again
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "Resend", style = discord.ButtonStyle.gray)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
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
    Modal that allows the user to enter a bet
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

# todo: make each button call different functions with some shared logic?
class ButtonsBetPhase(discord.ui.View):
    """
    Button set that allows players to bet
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "View Hand", style = discord.ButtonStyle.blurple)
    async def hit_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Let the user view their hand
        """
        print(f"{interaction.user} pressed {button.label}!")
        # send the user their hand
        current_player = self.manager.game.player_data[interaction.user]
        if len(current_player.hand) != 2:
            raise ValueError("Player hand must contain 2 cards")
        message = f"Your hand is {cards_to_str_52_standard(current_player.hand)}"
        await interaction.response.send_message(message, ephemeral = True, delete_after = 60)

    @discord.ui.button(label = "Call", style = discord.ButtonStyle.green)
    async def call(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Call
        """
        print(f"{interaction.user} pressed {button.label}!")
        await self.manager.make_bet(interaction, self.manager.game.largest_bet
            - self.manager.game.player_data[interaction.user].round_bet)

    @discord.ui.button(label = "Raise", style = discord.ButtonStyle.red)
    async def bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Allows the user to bring up the betting menu
        """
        print(f"{interaction.user} pressed {button.label}!")
        if not await self.manager.deny_non_participants(interaction):
            return
        await interaction.response.send_modal(BetModal(self.manager))

    @discord.ui.button(label = "Fold", style = discord.ButtonStyle.gray)
    async def fold(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Fold
        """
        print(f"{interaction.user} pressed {button.label}!")
        #Fold
        self.manager.game.player_data[interaction.user].active = False
        self.manager.game.active_player_turn_order.remove(interaction.user)
        self.manager.base_gui = None
        await interaction.response.send_message(f"{interaction.user.mention} has folded!")
        await self.next_player(interaction, True)


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
