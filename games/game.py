"""Abstract game classes

Defines abstract classes for the model and manager which are used to
control basic things that exist for all game types, such as starting,
players joining/leaving, ending the game, etc
"""


class BaseGame():
    """
    Game model class. Member vars should only be accessed by its manager or AI functions.
    """
    def __init__(self, game_type=0, player_list=None, game_state=0):
        # ID value of the game type
        self.game_type = game_type
        # list of players engaged with this game
        self.player_list = player_list
        # current game state, used to help manage certain outside interactions
        # game_state = 0 -> game is open to anyone at any time
        self.game_state = game_state

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
        return False


class GameManager():
    """
    Manages the most basic interactions for any game, such as creation, base menu
    management, etc. Should be subclassed by each game type's manager class.
    Methods can (and should) be overridden but be careful when doing so as to not
    break the default flow of all games
    """
    def __init__(self, game, base_gui, channel_id, factory, user_id, players=0, cpus=0):
        # hold the game model that this manager needs to manage (pass constructor to
        # subclass of BaseGame for that game)
        self.game = game
        # default button layout that the bot can use to construct the base menu at any time
        self.base_gui = base_gui
        # ID of the channel that this game is taking place in
        self.channel_id = channel_id
        # reference to the GameFactory class, needed to remove the game from the active games
        # dict upon the game ending
        self.factory = factory
        # user who called command
        self.user_id = user_id
        # amount of human players
        self.players = players
        # amount of computer players
        self.cpus = cpus
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
                                        self.get_base_menu_string(), view=self.base_gui)

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
        await self.factory.stop_game(self.channel_id)

    def get_base_menu_string(self):
        """
        Return a string that represents the current state of the game, as shown to
        ALL players. This method must be overridden
        """
        # might be a good idea to replace this with an exception
        return "Generic game menu message"

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
