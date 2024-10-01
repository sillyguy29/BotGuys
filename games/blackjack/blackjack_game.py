"""
Contains game/player data for blackjack games
"""
from games.game import BaseGame
from games.game import BasePlayer
from util import cards_to_str_52_standard

class BlackjackPlayer(BasePlayer):
    """
    Blackjack player class, contains everything specific to a player
    """
    def __init__(self):
        super().__init__()

        self.hand = []
        self.eleven_ace_count = 0
        self.hand_value = 0
        self.chips = 300
        self.current_bet = 0
        self.current_payout_multiplier = 1

    def reset(self):
        """
        Reset the player's stats after a game ends
        """
        self.hand.clear()
        self.eleven_ace_count = 0
        self.hand_value = 0
        self.current_bet = 0
        self.current_payout_multiplier = 1

    def get_debug_str(self):
        return (f"\t\thand: {self.hand}\n"
                f"\t\televen_ace_count: {self.eleven_ace_count}\n"
                f"\t\thand_value: {self.hand_value}\n"
                f"\t\tchips: {self.chips}\n"
                f"\t\tcurrent_bet: {self.current_bet}\n"
                f"\t\tcurrent_payout_multiplier: {self.current_payout_multiplier}\n")

    def get_bet_phase_str(self):
        """
        Convert the player's stats to a string to be used during the
        betting phase
        """
        return f"Chips: {self.chips}, Bet: {self.current_bet}"

    def get_play_phase_str(self):
        """
        Convert the player's stats to a string to be used during the
        play phase
        """
        if self.current_payout_multiplier == 2.5:
            return (f"({self.chips} chips, {self.current_bet} bet): "
                    f"{cards_to_str_52_standard(self.hand)} BLACKJACK!")
        elif self.current_payout_multiplier == 0:
            return (f"({self.chips} chips, {self.current_bet} bet): "
                    f"{cards_to_str_52_standard(self.hand)} BUST!")
        else:
            return (f"({self.chips} chips, {self.current_bet} bet): "
                    f"{cards_to_str_52_standard(self.hand)}")

    def get_payout_str(self):
        """
        Convert the player's stats into a string showing the player's
        payout for the round. Does not modify player stats.
        """
        return (f"{self.current_bet} x {self.current_payout_multiplier} = "
                f"{round(self.current_bet * self.current_payout_multiplier)} + {self.chips} = "
                f"{round(self.current_bet * self.current_payout_multiplier) + self.chips}")


class BlackjackGame(BaseGame):
    """
    Blackjack game model class. Keeps track of the turn order and dealer's hand
    """
    def __init__(self):
        # game state 1 -> accepting players but not playing yet
        super().__init__(game_type=1, player_data={}, game_state=1)

        self.turn_order = []
        self.dealer_hand = []
        self.dealer_hidden_card = None
        self.turn_index = -1
        self.betted_players = 0

    def get_active_player(self):
        """
        Returns the player whose turn it is, or None if not applicable
        """
        if self.turn_index == -1:
            return None
        return self.turn_order[self.turn_index]

    def get_debug_str(self):
        ret = super().get_debug_str()
        ret += ("Blackjack game attributes:\n"
                f"\tturn_order: {self.turn_order}\n"
                f"\tturn_index: {self.turn_index}\n"
                f"\tdealer_hand: {self.dealer_hand}\n"
                f"\tdealer_hidden_card: {self.dealer_hidden_card}\n")
        ret += self.get_player_debug_strs()
        return ret

    def get_player_debug_strs(self):
        ret = "Player data:\n"
        for player in self.player_data:
            ret += f"\tPlayer {player.display_name}:\n"
            ret += self.player_data[player].get_debug_str()
        return ret

    #def __repr__(self):
