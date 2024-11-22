"""
module containing most of views necessary for Uno
"""

import discord
from games.uno.uno_card import UnoCard

class UnoButtonsBase(discord.ui.View):
    """
    Base menu button group for the Uno game.
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
        will be deleted after it is interacted with or 10 seconds
        has passed (prevents menus that are not accounted for after
        game end).
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        await self.manager.add_player(interaction)

    @discord.ui.button(label="Settings", style= discord.ButtonStyle.blurple)
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        If the user that interacted with this menu is currently in the game, send
        an ephemeral message to the person who interacted with this
        menu a message which contains the submenu for selecting Uno Settings until
        the user dismisses it or the game starts or ends, otherwise do nothing.
        """
        self.manager.quick_log(f"{interaction.user} pressed {button.label}")
        await self.manager.bring_up_preferences_menu(interaction)

    @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Quit the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        # remove current players from active player list
        await self.manager.remove_player(interaction)

    @discord.ui.button(label = "Start Game", style = discord.ButtonStyle.blurple)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Start the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        # start the game
        await self.manager.start_game(interaction)

class UnoButtonsPreferences(discord.ui.View):
    """
    Provides the menu for adjusting uno settings on a per player basis
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "Exit Settings", style = discord.ButtonStyle.red)
    async def exit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        A place holder button for use until the uno preferences menu has actual
        settings management implemented.
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        # start the game
        await self.manager.close_preferences_menu(interaction)

class UnoButtonsBaseGame(discord.ui.View):
    """
    Menu includes "Show Hand" and "Draw"
    In the future: Include "Quit" button here as well.
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "Show Hand", style = discord.ButtonStyle.green)
    async def show_cards(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Send an ephemeral message to the person who interacted with
        this button that contains the show cards menu. This menu
        will be deleted after it is interacted with or 20 seconds
        has passed (prevents menus that are not accounted for after
        game end).
        """

        # Delete prior "Show Hand" menu so there isn't several lingering
        uno_player = self.manager.game.player_data[interaction.user]
        if uno_player.active_interaction:
            await uno_player.active_interaction.delete_original_response()
            uno_player.active_interaction = None

        # Send user a new "Show Hand" menu
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        view = UnoCardButtons(self.manager, interaction.user)
        await interaction.response.send_message("Your cards:", view = view, ephemeral = True)

        # We track this interaction so we can delete the message if player presses "Draw"
        #    rather than waiting for the message to delete itself after 20 seconds
        self.manager.game.player_data[interaction.user].active_interaction = interaction
        # wait for the view to call self.stop() before we move beyond this point
        await view.wait()
        # delete the response to the card button press (the UnoCardButtons UI message)
        await interaction.delete_original_response()
        self.manager.game.player_data[interaction.user].active_interaction = None

    @discord.ui.button(label = "Draw", style = discord.ButtonStyle.blurple)
    async def draw_card(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Sends a ephemeral message to the person who interacted with
        this button to inform him of what card he draw.
        """
        # Reject request to draw cards if button presser is not the current turn player
        current_turn_player = self.manager.game.turn_order[self.manager.game.turn_index]
        if interaction.user != current_turn_player:
            await interaction.response.send_mesage("Wait your turn.", ephemeral = True, \
                delete_after = 2)
            return

        # If there is an active "Show Hand" menu, we should delete it now
        uno_player = self.manager.game.player_data[interaction.user]
        if uno_player.active_interaction:
            await uno_player.active_interaction.delete_original_response()
            uno_player.active_interaction = None

        # If the button presser IS the turn player, do the following:
        player = self.manager.game.player_data[interaction.user]
        card_drawn = await self.manager.draw_cards(player)
        msg = button.label + "! You drew a " + self.manager.color_to_emoji(card_drawn) \
            + " " + card_drawn.value
        await interaction.response.send_message(msg, ephemeral = True,
            delete_after =
            self.manager.game.preferences_variables.get_value_of("Drawn card show time")
        )

        # Announce that player has opted to draw a card and proceed to next turn
        await self.manager.announce(str(interaction.user) + " is drawing a card...")
        await self.manager.next_turn()

class UnoCardButtons(discord.ui.View):
    """
    Creates private group of buttons representing the cards in a user's hand
    """
    def __init__(self, manager, player):
        super().__init__()
        self.manager = manager
        self.player_hand = self.manager.player_data[player]
        self.disabled_view = None

        current_turn_player = self.manager.game.turn_order[self.manager.game.turn_index]

        for card in self.player_hand:
            disabled = (
                player != current_turn_player) or (
                self.manager.can_play_card(card))
            #basic safety to prevent more than 25 buttons being added and causing the whole bot
            #to burn to death in the infernal flames of an api rejection
            if len(self.children) != 25:
                self.add_item(CardButton(self.manager, card, disabled))

class PreferencesQuitButton(discord.ui.Button):
    """
    Button class exclusively for the quit button in the uno preferences menu
    """
    def __init__(self, manager):
        super().__init__(style=discord.ButtonStyle.red,label="Exit Settings")
        self.manager = manager

    async def callback(self, interaction):
        self.manager.quick_log(f"{interaction.user} pressed {self.label}!")
        await self.manager.close_preferences_menu(interaction)

class CardButton(discord.ui.Button):
    """
    Button class that represents an individual card in a user's hand
    """
    def __init__(self, manager, card, disabled=True):
        super().__init__(style=discord.ButtonStyle.gray, label=f"{card.value}", \
            emoji=manager.color_to_emoji(card))
        self.manager = manager
        self.card = card
        self.disabled = disabled

    async def callback(self, interaction: discord.Interaction):
        self.manager.quick_log(f"{interaction.user} pressed {str(self.card)}!")
        assert self.view is not None
        view: UnoCardButtons = self.view
        await self.manager.play_card(interaction, self.card)
        view.stop()


class UnoWildCard(discord.ui.View):
    """
    This is the menu that appears when the player plays a Wild card
    to prompt them to select a color for the next card.
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    @discord.ui.button(label = "Red", style = discord.ButtonStyle.gray, emoji = "🔴")
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Changes the wild card to red.
        """
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        self.manager.game.top_card = UnoCard("Red", "Card")
        self.stop()

    @discord.ui.button(label = "Blue", style = discord.ButtonStyle.gray, emoji = "🔵")
    async def blue(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Changes the wild card to blue.
        """
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        self.manager.game.top_card = UnoCard("Blue", "Card")
        self.stop()

    @discord.ui.button(label = "Yellow", style = discord.ButtonStyle.gray, emoji = "🟡")
    async def yellow(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Changes the wild card to yellow.
        """
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        self.manager.game.top_card = UnoCard("Yellow", "Card")
        self.stop()

    @discord.ui.button(label = "Green", style = discord.ButtonStyle.gray, emoji = "🟢")
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Changes the wild card to green.
        """
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        self.manager.game.top_card = UnoCard("Green", "Card")
        self.stop()


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
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
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
        self.manager.quick_log(f"{interaction.user} pressed {button.label}!")
        # stop accepting input
        self.stop()
        await interaction.channel.send(f"{interaction.user.mention} ended the game!")
        await self.manager.quit_game(interaction)
