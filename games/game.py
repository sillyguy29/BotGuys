"""Abstract game classes

Defines abstract classes for the model and manager which are used to
control basic things that exist for all game types, such as starting,
players joining/leaving, ending the game, etc
"""
import logging
import discord
from util import send_info_message

class BasePlayer():
    """
    Generic player data class
    """
    def __init__(self):
        return

    def get_debug_str(self):
        """
        Overridden by subclasses
        """
        return ""


class BaseGame():
    """
    Game model class. Member vars should only be accessed by its manager or AI functions.
    """
    def __init__(self, game_type=0, player_data=None, game_state=0,
                 user_id=None, players=0, cpus=0, max_players=0):
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

    def user_in_game(self, player):
        """
        Returns a bool indicating whether a player is in the game
        """
        if self.game_state == 0:
            return True
        else:
            return player in self.player_data

    def get_active_player(self):
        """
        Get the player whose turn it is, or none if there is no turn
        order currently
        """
        return None

    def get_debug_str(self):
        """
        Returns a string with all members of the class for debug
        """
        return ("Base game attributes:\n"
        f"\tgame_type: {self.game_type}\n"
        f"\tuser_id: {self.user_id}\n"
        f"\tplayers: {self.players}\n"
        f"\tcpus: {self.cpus}\n"
        f"\tgame_state: {self.game_state}\n"
        f"\tmax_players: {self.max_players}\n")

class GameManager():
    """
    Manages the most basic interactions for any game, such as creation, base menu
    management, etc. Should be subclassed by each game type's manager class.
    Methods can (and should) be overridden but be careful when doing so as to not
    break the default flow of all games
    """
    def __init__(self, game, base_gui, channel, factory, preferences_gui=None):
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
        # preferences menu layout
        self.preferences_gui = preferences_gui

    async def create_game(self, interaction):
        """
        Send the base menu for the first time. The interaction passed in should be
        the slash command that started the game
        """
        self.quick_log("Creating game")
        # construct the first base menu message, grabbing the buttons from self.base_gui
        # and the message contents from self.get_base_menu_string
        await interaction.response.send_message(content=self.get_base_menu_string(),
                                                view=self.base_gui, silent=True)
        # set our base menu message to the message that the interaction (ie the slash command
        # that started the game) was responded with (the base menu created by this interaction)
        self.current_active_menu = await interaction.original_response()

    async def refresh(self, interaction):
        """
        Edit the active base menu to reflect the current game state
        """
        self.quick_log("Refreshing base menu")
        # check to make sure the game hasn't ended, do nothing if it has
        if await self.game_end_check(interaction):
            return

        await self.current_active_menu.edit(content=self.get_base_menu_string(),
                                            view=self.base_gui)
        self.quick_log("Base menu refreshed")

    async def resend(self, interaction):
        """
        Remove the buttons from the current active base menu and send a new one
        """
        self.quick_log("Resending base menu")
        # check to make sure the game hasn't ended, do nothing if it has
        if await self.game_end_check(interaction):
            return

        # removes the view (which contains the buttons) from the current active base menu
        await self.current_active_menu.edit(view=None)
        # InteractionMessage inherits from Message so we can access the channel attribute to
        # send a new base menu into
        self.current_active_menu = await self.channel.send(self.get_base_menu_string(),
                                                           view=self.base_gui, silent=True)
        self.quick_log("Base menu resent")

    async def preferences_menu(self, interaction):
        """
        This is the Game manager call for preferences menu
        it should almost certainly not have been called.
        """
        self.quick_log("preferences_menu in GameManager called.")
        await interaction.response.send_message(content="No preferences menu for this game.",
            silent=True, ephemeral=True, delete_after=2)

    async def quit_game(self, interaction):
        """
        Stop the game by removing the buttons from its current active base menu and
        asking the game factory to remove it from the dictionary. Set its game state
        to -1, meaning the game is over
        """
        # check to make sure we haven't already ended, do nothing if we have
        if await self.game_end_check(interaction):
            return

        self.quick_log("Initiating game end process")
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

    def get_player_data(self, player):
        """
        Return player data object. DO NOT modify this object directly.
        Doing so breaks encapsulation. Only modify through the manager.
        """
        return self.game.player_data[player]

    def user_in_game(self, player):
        """
        Returns a boolean value indicating whether the player is in
        the game
        """
        return self.game.user_in_game(player)

    def get_active_player(self):
        """
        Returns the user object of whoever's turn it is in the game,
        none if there is no turn order
        """
        return self.game.get_active_player()

    async def deny_non_participants(self, interaction):
        """
        Quick shortcut to deny players who are not in a game.
        Returns True if they are in game, else returns False.

        Uses interaction if the player is not in the game, otherwise
        it does not use the interaction.
        """
        if interaction.user not in self.game.player_data:
            await interaction.response.send_message("You are not in this game.",
                                                    ephemeral=True, delete_after=10)
            return False
        return True

    async def add_player(self, interaction, init_player_data=None):
        """
        Check whether a player can be added to the game in its current state, and if so,
        add them and associate them with init_player_data.
        """
        self.quick_log("Attempting to join game", interaction)
        # see if game has already ended, return if it has
        if await self.game_end_check(interaction):
            return

        if self.game.game_state == 0:
            self.quick_log("Couldn't join game (open game)", interaction)
            await send_info_message("This game is open to any player at any time.", interaction)

        elif self.game.game_state in (1, 2):
            if self.user_in_game(interaction.user):
                self.quick_log("Couldn't join game (already joined)", interaction)
                await send_info_message("You are already in this game.", interaction)
            else:
                self.game.players += 1
                self.game.player_data[interaction.user] = init_player_data
                await interaction.response.send_message((f"{interaction.user.mention} "
                                                         "joined the game!"))
                self.quick_log("Joined game successfully", interaction)

        else:
            self.quick_log("Couldn't join game (bad gs)", interaction)
            await send_info_message("This game is not currently accepting players.", interaction)

    async def remove_player(self, interaction):
        """
        Check whether a player can leave the game in its current state, and if so, remove
        """
        self.quick_log("Attempting to leave game", interaction)

        # see if game has already ended, return if it has
        if await self.game_end_check(interaction):
            return

        if self.game.game_state == 0:
            self.quick_log("Couldn't leave game (open game)", interaction)
            await send_info_message("This game is open to any player at any time.", interaction)

        elif not self.user_in_game(interaction.user):
            self.quick_log("Couldn't leave game (not in game)", interaction)
            await send_info_message("You are not in this game.", interaction)

        elif self.game.game_state in (1, 3):
            self.game.players -= 1
            self.game.player_data.pop(interaction.user)
            await interaction.response.send_message((f"{interaction.user.mention} "
                                                    "left the game!"))
            self.quick_log("Left game successfully", interaction)

        else:
            self.quick_log("Couldn't leave game (bad gs)", interaction)
            await send_info_message("You cannot leave this game right now.", interaction)

    async def game_end_check(self, interaction):
        """
        Check and see if a game has ended. Pass in an interaction that
        might occur after a game has ended so that we can check to make
        sure that it is valid and notify the user if it is not.
        """
        # if the game has ended, notify the user and don't do anything
        if self.game.has_ended():
            await send_info_message("This game has ended.", interaction)
            # True -> game has ended
            return True
        # False -> game has not ended
        return False

    async def interaction_is_valid(self, interaction=None, turn_order=False,
                                   in_game=True, game_end=True):
        """
        Runs through a series of checks to determine if an interaction
        is valid. Responds to the interaction and returns False if this
        interaction was not valid. Prevents unexpected interactions
        from modifying state.

        Arguments are the various types of checks that this function
        performs. Here are the checks:
        - turn_order: Defaults to False. Checks if it's the player's
        turn.
        - in_game: Defaults to True. Checks if the player is in the
        game.
        - game_end: defaults to True. Checks if the game has ended.
        """
        self.quick_log("Checking interaction validity", interaction)

        if interaction is None:
            self.quick_log("Interaction validity check failed (interaction=None)")
            return False

        if game_end:
            if self.game.game_state == -1:
                self.quick_log("Interaction validity check failed (game_end)", interaction)
                await send_info_message("This game has ended.", interaction)
                return False

        if in_game:
            if not self.user_in_game(interaction.user):
                self.quick_log("Interaction validity check failed (in_game)", interaction)
                await send_info_message("You are not in this game.", interaction)
                return False

        if turn_order:
            if self.get_active_player() != interaction.user:
                self.quick_log("Interaction validity check failed (turn_order)", interaction)
                await send_info_message("It's not your turn.", interaction)
                return False

        self.quick_log("Interaction validity check succeeded", interaction)
        return True

    def get_debug_str(self):
        """
        Returns a string with all members of the class for debug
        """
        return ("Base manager:\n"
                f"\tbase_gui: {self.base_gui}\n"
                f"\tchannel id: {self.channel.id}\n" + self.game.get_debug_str())

    def quick_log(self, content, interaction=None, level=logging.DEBUG):
        """
        Sends a log that has useful information already applied to it.
        The default logging level is debug. Override with level arg.
        Normally appends channel id, game type, and game state, but can
        also append a username if an interaction is passed.
        """
        log_content = f"[{self.channel.id}](gt,gs:{self.game.game_type},{self.game.game_state})"
        if interaction is not None:
            log_content += f"(user:{interaction.user}) " + content
        else:
            log_content += " " + content

        logging.log(level, log_content)
