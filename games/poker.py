"""Poker game module

Contains all the logic needed to run a game of Texas Hold'em Poker.
It features an closed game model, meaning not all users can interact
with the game at any time, and there is player management.
"""
import discord
from games.game import BaseGame
from games.game import GameManager
from games.game import BasePlayer
from util import Card
from util import generate_deck
import random

class PokerPlayer(BasePlayer):
    def __init__(self, is_cpu=False):
        super().__init__()
        self.hand = []
        self.chips = 0
        self.bet = 0
        self.is_cpu = is_cpu
        self.active = True #Inactive when they fold

class PokerGame(BaseGame):
    """
    Poker game model class. Keeps track of the deck and none else
    """
    def __init__(self):
        # game state 1 -> accepting players but not playing yet
        super().__init__(game_type=1, player_data={}, game_state=1)
        
        self.deck = generate_deck()
        self.dealer_hand = []
        random.shuffle(self.deck)

    #def __repr__(self):
 
        
class PokerManager(GameManager):
    def __init__(self, factory, channel_id, user_id):
        super().__init__(PokerGame(), PokerButtonsBase(self),
                         channel_id, factory)
        
        # What is player_list? We have player_data (dict) in the game model
        self.game.player_list.append(user_id)

    async def create_game(self, interaction):
        raise NotImplementedError("Override this method based on Poker specifications")
    
    async def start_game(self, interaction):
        # game_state == 4 -> players cannot join or leave
        self.game.game_state = 4
        await self.gameplay_loop()
        
    def get_base_menu_string(self):
        if self.game.game_state == 1:
            return "Welcome to this game of Poker. Feel free to join."
        elif self.game.game_state == 4:
            return "Game has started, placeholder string"

        
    async def remove_all_players(self):
        """
        Removes all players from the players list
        """
        await self.factory.remove_players(self.game.player_list)

    async def gameplay_loop(self):
        """
        The main gameplay loop for the Poker game
        """
        pass

     
class PokerButtonsBase(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
    
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
        # TODO: the second arg should contain a class or data structure that contains
        # all the data needed for a player in this game
        if self.manager.game.is_accepting_players():
            indi_player_data = PokerPlayer()
            await self.manager.add_player(interaction, indi_player_data)
        else:
            await interaction.response.send_message("This game is not currently accepting players.",
                                                     ephemeral = True, delete_after = 10)
    
    @discord.ui.button(label = "Quit", style = discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Quit the game
        """
        # print when someone presses the button because otherwise
        # pylint won't shut up about button being unused
        print(f"{interaction.user} pressed {button.label}!")
        # remove current players from active player list
        self.manager.remove_player(interaction)
        # if nobody else is left, then quit the game
        if self.game.players == 0:
            await self.manager.quit_game(interaction)

    @discord.ui.button(label = "Start game", style = discord.ButtonStyle.blurple)
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
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

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

class ViewHand(discord.ui.View):
    """
    Button group that just shows "View Hand" button
    View Hand should send ephemeral message of the user's hand
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    @discord.ui.button(label = "View Hand", style = discord.ButtonStyle.green)
    async def hit_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Let the user view their hand
        """
        print(f"{interaction.user} pressed {button.label}!")
        # stop accepting interactions for this message
        self.stop()
        # send the user their hand
        current_player = self.manager.game.player_data[interaction.user]
        if len(current_player.hand) != 2:
            raise ValueError("Player hand must contain 2 cards")
        await interaction.response.send_message(f"Your hand is {str(current_player.hand[0])} and {str(current_player.hand[1])}", ephemeral = True, delete_after = 60)

class DecideBet(discord.ui.View):
    """
    Button group to decide value of bet
    Should be 5 buttons: +10, +1, -1, -10, and Done
    """
    def __init__(self, manager, min_bet = 0):
        super().__init__()
        self.manager = manager
        self.bet = 0
        self.min_bet = min_bet

    @discord.ui.button(label = "+10", style = discord.ButtonStyle.green)
    async def plus_10(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Raise bet by 10
        """
        print(f"{interaction.user} pressed {button.label}!")
        # stop accepting interactions for this message
        self.stop()
        #TODO: raise bet by 10, should edit a message that shows the current bet
        #TODO: add +1, -1, -10 buttons with very similar code.
        if self.bet + 10 <= self.manager.game.player_data[interaction.user].chips:
            self.bet += 10

    @discord.ui.button(label = "Done", style = discord.ButtonStyle.blurple)
    async def enter_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Enter bet
        """
        print(f"{interaction.user} pressed {button.label}!")
        # stop accepting interactions for this message
        self.stop()
        #TODO: enter bet, should move on to next person after bet is made

class StandardTurnButtons(discord.ui.View):
    """
    Button group for the options to Call, Raise, or Fold
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    @discord.ui.button(label = "Call", style = discord.ButtonStyle.gray)
    async def call(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Call
        """
        print(f"{interaction.user} pressed {button.label}!")
        # stop accepting interactions for this message
        self.stop()
        # User bets the amount needed to match the current bet
        #TODO: What if the user doesn't have enough chips to call?

    @discord.ui.button(label = "Raise", style = discord.ButtonStyle.green)
    async def raise_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Raise
        """
        print(f"{interaction.user} pressed {button.label}!")
        # stop accepting interactions for this message
        self.stop()
        #TODO: Ask the user to make a bet

    @discord.ui.button(label = "Fold", style = discord.ButtonStyle.red)
    async def fold(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Fold
        """
        print(f"{interaction.user} pressed {button.label}!")
        # stop accepting interactions for this message
        self.stop()
        #TODO: Fold stuff



def encode_hand_value(hand_tuple):
    """
    hand_tuple is the tuple of values corresponding to the value of a hand
    along with any values necessary for breaking ties
    Returns an integer that can be used for comparing hands
    """
    # This uses powers of 13 because there are 13 possible card faces
    # Essentially encodes the values as a base 13 number
    # This should make comparing more than 2 hands at a time easier
    # Also avoids the creation of a new data type
    return_value = hand_tuple[0] * (13**5)
    for index in range(1, len(hand_tuple)):
        return_value += hand_tuple[index] * (13 ** (5-index))
    return return_value

def max_hand(hand):
    """
    Returns the maximum hand value of a given hand,
    along with information necessary for breaking ties
    hand: list of 5 Card objects
    """
    lookup = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J","Q", "K", "A")
    alt_lookup = ("A",) + lookup[:12] #Used in checking Straight Flush and Straights for A=1
    if len(hand) != 5:
        raise ValueError("Hand must contain 5 cards")
    hand.sort(key = lambda x: lookup.index(x.face))
    same_suit = True
    for c in hand:
        if c.suit != hand[0].suit:
            same_suit = False
            break
    highest_value = lookup.index(hand[4].face)

    #Check Royal Flush
    if same_suit:
        if hand[0].face == "10" and hand[1].face == "J" and hand[2].face == "Q" and hand[3].face == "K" and hand[4].face == "A":
            return encode_hand_value((10, highest_value))
    
    #Check Straight Flush
    if same_suit:
        #Straight Flush uses alt_lookup because if it is not a Royal Flush, A=1 if it is a Flush
        is_straight = True
        for index in range(4):
            if alt_lookup.index(hand[index].face) + 1 != alt_lookup.index(hand[index + 1].face):
                is_straight = False
                break
        if is_straight:
            return encode_hand_value((9, highest_value))
    
    num_same = 0
    type_dict = dict()
    for c in hand:
        type_dict[c.face] = type_dict.get(c.face, 0) + 1

    #Check Four of a Kind
    for key in type_dict:
        if type_dict[key] == 4:
            for key2 in type_dict:
                if key2 != key:
                    return encode_hand_value((8, lookup.index(key), lookup.index(key2)))
        
    #Check Full House
    for key in type_dict:
        if type_dict[key] == 3:
            for key2 in type_dict:
                if type_dict[key2] == 2:
                    return encode_hand_value((7, lookup.index(key), lookup.index(key2)))
                
    #Check Flush
    if same_suit:
        return encode_hand_value((6, ) + tuple(sorted([lookup.index(c.face) for c in hand], reverse = True)))
    
    #Check Straight
    is_high_straight = True
    for index in range(4):
        if lookup.index(hand[index].face) + 1 != lookup.index(hand[index + 1].face):
            is_high_straight = False
            break
    is_low_straight = True
    for index in range(4):
        if alt_lookup.index(hand[index].face) + 1 != alt_lookup.index(hand[index + 1].face):
            is_low_straight = False
            break
    if is_high_straight:
        return encode_hand_value((5, highest_value))
    elif is_low_straight:
        # We use '3' here because if it is a low straight, A=1 and the highest value card
        # is 5 (A,2,3,4,5), which is 3 in the primary lookup list [2,3,4,5,...,A]
        return encode_hand_value((5, 3))
    
    #Check Three of a Kind
    for key in type_dict:
        if type_dict[key] == 3:
            for key2 in type_dict:
                if key2 != key:
                    for key3 in type_dict:
                        if key3 != key and key3 != key2:
                            return encode_hand_value((4, lookup.index(key), lookup.index(key2), lookup.index(key3)))
    
    #Check Two Pair
    num_pairs = 0
    for key in type_dict:
        if type_dict[key] == 2:
            num_pairs += 1
    if num_pairs == 2:
        pair_values = []
        kicker = 0
        for key in type_dict:
            if type_dict[key] == 2:
                pair_values.append(lookup.index(key))
            else:
                kicker = lookup.index(key)
        return encode_hand_value((3, ) + tuple(sorted(pair_values, reverse = True)) + (kicker, ))
    
    #Check One Pair
    if num_pairs == 1:
        pair_value = 0
        kicker_values = []
        for key in type_dict:
            if type_dict[key] == 2:
                pair_value = lookup.index(key)
            else:
                kicker_values.append(lookup.index(key))
        return encode_hand_value((2, pair_value) + tuple(sorted(kicker_values, reverse = True)))
    
    #No good hand, must use high card
    return encode_hand_value((1, ) + tuple(sorted([lookup.index(c.face) for c in hand], reverse = True)))

def compare_hands(hand1, hand2):
    """
    Returns 1 if hand1 is better, 2 if hand2 is better, 0 if tie
    hand1 and hand2 are both lists of 5 Card objects
    """
    hand1_value = max_hand(hand1)
    hand2_value = max_hand(hand2)
    if hand1_value > hand2_value:
        return 1
    elif hand1_value < hand2_value:
        return 2
    return 0