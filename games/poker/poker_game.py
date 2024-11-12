import random
from games.game import BaseGame
from games.game import BasePlayer
from util import generate_deck

class PokerPlayer(BasePlayer):
    """
    Represents a player in a game of poker.
    A brief overview of its attributes and methods:
    Attributes:
    1. hand (list): The player's hand of cards.
    2. chips (int): The number of chips the player has.
    3. round_bet (int): The amount of chips the player has bet in the current round.
    4. total_bet (int): The total amount of chips the player has bet.
    5. is_cpu (bool): Specifies whether the player is controlled by the CPU.
    6. active (bool): Specifies whether the player is active in the game.
    Methods:
    1. get_debug_str: Returns a string representation of the player's debug information.
    """
    def __init__(self, is_cpu=False):
        """
        Initializes a PokerPlayer object.

        Args:
            is_cpu (bool, optional): Specifies whether the player is controlled 
            by the CPU. Defaults to False.
        """
        super().__init__()
        self.hand = []
        self.chips = 10000
        self.round_bet = 0
        self.total_bet = 0
        self.is_cpu = is_cpu
        self.active = True #Inactive when they fold

    def get_debug_str(self):
        """
        Returns a string representation of the player's debug information.

        Returns:
            str: A string containing the hand, chips, round bet, total bet, and active status.
        """
        return (f"\t\thand: {self.hand}\n"
                f"\t\tchips: {self.chips}\n"
                f"\t\tround_bet: {self.round_bet}\n"
                f"\t\ttotal_bet: {self.total_bet}\n"
                f"\t\tactive: {self.active}\n")

class PokerGame(BaseGame):
    """
    Represents a game of poker.
    A brief overview of its attributes and methods:
    Attributes:
    1. deck (list): The deck of cards.
    2. community_cards (list): The community cards.
    3. pool (int): The number of chips in the pool.
    4. largest_bet (int): The largest bet in the current round.
    5. turn_order (list): The order of players in the game.
    6. active_player_turn_order (list): The order of active players in the game.
    7. turn_index (int): The index of the current player in the turn order.
    8. best_hand (list): The best hand in the game.
    9. winner (dict): The winner of the game.
    Methods:
    1. get_debug_str: Returns a string representation of the game's debug information.
    2. get_player_debug_strs: Returns a string representation of player data for debugging purposes.
    """
    def __init__(self, cpus):
        super().__init__(game_type=1, player_data={}, game_state=1, cpus=cpus)
        self.community_cards = []
        self.pool = 0
        self.largest_bet = 0
        self.turn_order = []
        self.active_player_turn_order = []
        self.turn_index = 0
        self.best_hand = []
        self.winner = {}

    def get_debug_str(self):
        ret = super().get_debug_str()
        ret += ("Poker game attributes:\n"
                f"\tcommunity: {self.community_cards}\n"
                f"\tpool: {self.pool}\n"
                f"\tlargest_bet: {self.largest_bet}\n"
                f"\tturn_order: {self.turn_order}\n"
                f"\tactive_turn_order: {self.active_player_turn_order}\n"
                )
        ret += self.get_player_debug_strs()
        return ret

    def get_player_debug_strs(self):
        """
        Returns a string representation of the player data for debugging purposes.

        Returns:
            str: A string containing the player data.
        """
        ret = "Player data:\n"
        for player in self.player_data:
            ret += f"\tPlayer {player.display_name}:\n"
            ret += self.player_data[player].get_debug_str()
        return ret
