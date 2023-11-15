"""Abstract game classes

Defines abstract classes for the model and manager which are used to
control basic things that exist for all game types, such as starting,
players joining/leaving, ending the game, etc
"""
import discord

class BasePlayer():
    """
    Generic player data class
    """
    def __init__(self):
        return


class BaseGame():
    """
    Game model class. Member vars should only be accessed by its manager or AI functions.
    """
    def __init__(self, game_type=0, player_data=None, game_state=0, user_id=None, players=0, cpus=0, max_players=0):
        # ID value of the game type
        self.game_type = game_type
        # list of players engaged with this game
        self.player_data = player_data
        # user who called command
        self.user_id = user_id
        # amount of human players
        self.players = players
        # amount of computer players
        self.cpus = cpus
        # current game state, used to help manage certain outside interactions
        # game_state = 0 -> game is open to anyone at any time
        self.game_state = game_state
        self.max_players = max_players

    def has_ended(self):
        """
        Checks game state to see if the game has ended
        """
        return self.game_state == -1

    def is_accepting_players(self):
        """
        Returns bool corresponding to whether the game is accepting new
        players
        """
        # counter is an open game, and thus does not accept players
        # change method to check game state upon non-open games being
        # made
        return self.max_players > self.players


class GameManager():
    """
    Manages the most basic interactions for any game, such as creation, base menu
    management, etc. Should be subclassed by each game type's manager class.
    Methods can (and should) be overridden but be careful when doing so as to not
    break the default flow of all games
    """
    def __init__(self, game, base_gui, channel, factory):
        # hold the game model that this manager needs to manage (pass constructor to
        # subclass of BaseGame for that game)
        self.game = game
        # default button layout that the bot can use to construct the base menu at any time
        self.base_gui = base_gui
        # ID of the channel that this game is taking place in
        self.channel = channel
        # reference to the GameFactory class, needed to remove the game from the active games
        # dict upon the game ending
        self.factory = factory
        # reference to the message that currently contains the base menu. Needed so that the
        # bot can remove the buttons from it or edit its contents at any time
        self.current_active_menu = None

    async def create_game(self, interaction):
        """
        Send the base menu for the first time. The interaction passed in should be
        the slash command that started the game
        """
        # construct the first base menu message, grabbing the buttons from self.base_gui
        # and the message contents from self.get_base_menu_string
        await interaction.response.send_message(content=self.get_base_menu_string(),
                                                view=self.base_gui)
        # set our base menu message to the message that the interaction (ie the slash command
        # that started the game) was responded with (the base menu created by this interaction)
        self.current_active_menu = await interaction.original_response()

    async def refresh(self, interaction):
        """
        Edit the active base menu to reflect the current game state
        """
        # check to make sure the game hasn't ended, do nothing if it has
        if await self.game_end_check(interaction):
            return

        await self.current_active_menu.edit(content=self.get_base_menu_string(),
                                            view=self.base_gui)

    async def resend(self, interaction):
        """
        Remove the buttons from the current active base menu and send a new one
        """
        # check to make sure the game hasn't ended, do nothing if it has
        if await self.game_end_check(interaction):
            return

        # removes the view (which contains the buttons) from the current active base menu
        await self.current_active_menu.edit(view=None)
        # InteractionMessage inherits from Message so we can access the channel attribute to
        # send a new base menu into
        self.current_active_menu = await self.current_active_menu.channel.send(
                                        self.get_base_menu_string(), view=self.base_gui,
                                        silent=True)

    async def quit_game(self, interaction):
        """
        Stop the game by removing the buttons from its current active base menu and
        asking the game factory to remove it from the dictionary. Set its game state
        to -1, meaning the game is over
        """
        # check to make sure we haven't already ended, do nothing if we have
        if await self.game_end_check(interaction):
            return

        self.game.game_state = -1
        await self.current_active_menu.edit(view=None)
        await self.factory.stop_game(self.channel.id)
        # now we just pray that python's garbage collection notices this

    def get_base_menu_string(self):
        """
        Return a string that represents the current state of the game, as shown to
        ALL players. This method must be overridden
        """
        # might be a good idea to replace this with an exception
        return "Generic game menu message"

    async def add_player(self, interaction, init_player_data=None):
        """
        Check whether a player can be added to the game in its current state, and if so,
        add them and associate them with init_player_data.
        """
        # see if game has already ended, return if it has
        if await self.game_end_check(interaction):
            return

        if self.game.game_state == 0:
            await interaction.response.send_message("This game is open to any player at any time.",
                                                     ephemeral = True, delete_after = 10)
        elif self.game.game_state in (1, 2):
            if interaction.user in self.game.player_data:
                await interaction.response.send_message("You are already in this game.",
                                                        ephemeral = True, delete_after = 10)
            else:
                self.game.players += 1
                self.game.player_data[interaction.user] = init_player_data
                await interaction.response.send_message("Joined game.", ephemeral = True, 
                                                        delete_after = 10)
        else:
            await interaction.response.send_message("This game is not currently accepting players.",
                                                     ephemeral = True, delete_after = 10)

    async def remove_player(self, interaction):
        """
        Check whether a player can leave the game in its current state, and if so, remove
        """
        # see if game has already ended, return if it has
        if await self.game_end_check(interaction):
            return

        if self.game.game_state == 0:
            await interaction.response.send_message("This game is open to any player at any time.",
                                                     ephemeral = True, delete_after = 10)
        elif interaction.user not in self.game.player_data:
            await interaction.response.send_message("You are not in this game.",
                                                     ephemeral = True, delete_after = 10)
        elif self.game.game_state in (1, 3):
            self.game.players -= 1
            self.game.player_data.pop(interaction.user)
            await interaction.response.send_message("Left game.", ephemeral=True, delete_after=10)
        else:
            await interaction.response.send_message("You cannot leave this game right now.",
                                                     ephemeral = True, delete_after = 10)

    async def game_end_check(self, interaction):
        """
        Check and see if a game has ended. Pass in an interaction that
        might occur after a game has ended so that we can check to make
        sure that it is valid and notify the user if it is not.
        """
        # if the game has ended, notify the user and don't do anything
        if self.game.has_ended():
            await interaction.response.send_message("This game has ended.",
                                                    ephemeral = True,
                                                    delete_after = 10)
            # True -> game has ended
            return True
        # False -> game has not ended
        return False
    

#async def double_check(interaction):


class AreYouSureButtons(discord.ui.View):
    """
    Helper class designed to facilitate a double check from the user upon trying to perform
    certain actions
    """
    @discord.ui.button(label = "Yes", style = discord.ButtonStyle.green)
    async def yes_pressed(self, interaction: discord.Interaction, button: discord.ui.Button):
        return (True, interaction)
    
    @discord.ui.button(label = "No", style = discord.ButtonStyle.red)
    async def no_pressed(self, interaction: discord.Interaction, button: discord.ui.Button):
        return (False, interaction)