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
from util import double_check
from util import STANDARD_52_DECK
from util import cards_to_str_52_standard
from util import send_info_message
from util import generate_deck
import random
from itertools import combinations

class PokerPlayer(BasePlayer):
    def __init__(self, is_cpu=False):
        super().__init__()
        self.hand = []
        self.chips = 10000
        self.round_bet = 0
        self.total_bet = 0
        self.is_cpu = is_cpu
        self.active = True #Inactive when they fold

    def get_debug_str(self):
        return (f"\t\thand: {self.hand}\n"
                f"\t\tchips: {self.chips}\n"
                f"\t\tround_bet: {self.round_bet}\n"
                f"\t\ttotal_bet: {self.total_bet}\n"
                f"\t\tactive: {self.active}\n")

class PokerGame(BaseGame):
    """
    Poker game model class. Keeps track of the deck and bets
    """
    def __init__(self, cpus):
        # game state 1 -> accepting players but not playing yet
        super().__init__(game_type=1, player_data={}, game_state=1, cpus=cpus)
        
        self.deck = generate_deck()
        self.community_cards = []
        self.pool = 0
        self.largest_bet = 0
        self.turn_order = []
        self.turn_index = 0
        self.best_hand = []
        random.shuffle(self.deck)
    

    def get_debug_str(self):
        ret = super().get_debug_str()
        ret += ("Poker game attributes:\n"
                f"\tcommunity: {self.community_cards}\n"
                f"\tpool: {self.pool}\n"
                f"\tlargest_bet: {self.largest_bet}\n"
                f"\tturn_order: {self.turn_order}\n")
        ret += self.get_player_debug_strs()
        return ret

    def get_player_debug_strs(self):
        ret = "Player data:\n"
        for player in self.player_data:
            ret += f"\tPlayer {player.display_name}:\n"
            ret += self.player_data[player].get_debug_str()
        return ret    

    #def __repr__(self):
 
        
class PokerManager(GameManager):
    def __init__(self, factory, channel, cpus):
        super().__init__(game=PokerGame(cpus), base_gui=PokerButtonsBase(self),
                         channel=channel, factory=factory)

    async def add_player(self, interaction, init_player_data=None):
        await super().add_player(interaction, init_player_data)
        if interaction.user in self.game.player_data \
        and interaction.user not in self.game.turn_order:
            self.game.turn_order.append(interaction.user)

    async def remove_player(self, interaction):
        await super().remove_player(interaction)
        if interaction.user not in self.game.player_data \
        and interaction.user in self.game.turn_order:
            self.game.turn_order.remove(interaction.user)
        # if nobody else is left, then quit the game
        if self.game.players == 0:
            await self.quit_game(interaction)

    async def start_game(self, interaction):
        if self.game.game_state != 1:
            await send_info_message("This game has already started", interaction)
            return
        # game_state == 4 -> players cannot join or leave
        self.game.game_state = 4
        # swap default GUI to betting phase buttons
        await interaction.channel.send(f"{interaction.user.display_name} started the game!")
        await self.deal_cards(interaction)
        await self.resend(interaction)

    async def deal_cards(self, interaction):
        # make sure we're at the end of the betting phase
        if self.game.game_state != 4:
            return
        # game_state 5 -> dealing phase (players cannot join or leave)
        self.game.game_state = 5

        await interaction.channel.send("Dealing cards...")

        # draw 2 cards for every player
        for i in self.game.player_data:
            self.game.player_data[i].hand.extend(STANDARD_52_DECK.draw(2))

        self.base_gui = ButtonsBetPhase(self, self.game.players)

    async def make_bet(self, interaction, bet_amount):
        """
        Set a player's bet
        """
        # checks to see if the game is over
        if await self.game_end_check(interaction):
            return
        
        # check to see if it is the user's turn
        user = interaction.user
        if self.game.turn_order[self.game.turn_index] != user:
            await send_info_message("This is not your turn yet.", interaction)
            return 

        # check to see if the user can bet, and deny them if not
        user_data = self.game.player_data[user]
        if int(bet_amount) > user_data.chips:
            await send_info_message("You cannot afford this bet.", interaction)
            return

        # double check to make sure the user wants to confirm this bet
        (yes_clicked, interaction) = await double_check(interaction=interaction,
                                                    message_content=f"Betting {str(bet_amount)}.")
        if not yes_clicked:
            await send_info_message("Cancelled bet!", interaction)
            return
        # perform the bet
        user_data.round_bet = int(bet_amount)
        user_data.total_bet += int(bet_amount)
        self.game.pool += int(bet_amount)
        user_data.chips -= int(bet_amount)
        if int(bet_amount) >= self.game.largest_bet:
            self.game.largest_bet = int(bet_amount)
        await interaction.channel.send((f"{user.mention} has bet {str(bet_amount)} "
                                        f"chips and now has {str(user_data.chips)} "
                                        "chips left!"))
        await self.base_gui.next_player(interaction)
        return
    
    async def deal_table(self, interaction):
        if len(self.game.community_cards) == 0:
           self.game.community_cards.extend(STANDARD_52_DECK.draw(3))

        elif len(self.game.community_cards) == 5:
            await self.finalize_game(interaction)
        else:
            self.game.community_cards.extend(STANDARD_52_DECK.draw(1))
        await self.resend(interaction)
        return
    
    async def finalize_game(self, interaction):
        self.game.game_state = 7
        self.base_gui = None

        winning_hand = []
        winner = {}
        for player in self.game.player_data:
            if not winning_hand:
                winning_hand = self.game.player_data[player].hand
                winner = player.display_name
                self.game.best_hand = winning_hand
            else:
                if compare_hands(winning_hand, player.hand):
                    winning_hand = self.game.player_data[player].hand
                    winner = player.display_name
                    self.game.best_hand = winning_hand

        await interaction.response.send_message(f"{winner} has WON!") 
        return

    def get_base_menu_string(self):
        if self.game.game_state == 1:
            return "Who's ready for a game of poker?"

        elif self.game.game_state == 4:
            ret = "Current bets and chips:\n"
            for player in self.game.turn_order:
                player_data = self.game.player_data[player]
                ret += f"{player.display_name}: {player_data.get_bet_phase_str()}\n"
            return ret

        elif self.game.game_state == 5:
            ret = "Largest bet:\n"
            ret += f"{self.game.largest_bet}\n"
            ret += "Pool:\n"
            ret += f"{self.game.pool}\n"
            return ret
        
        elif self.game.game_state == 6:
            ret = "Community cards:\n"
            ret += f"{cards_to_str_52_standard(self.game.community_cards)}\n"
            ret += "Largest bet:\n"
            ret += f"{self.game.largest_bet}\n"
            ret += "Pool:\n"
            ret += f"{self.game.pool}\n"
            return ret
        
        elif self.game.game_state == 7:
            ret = "Winning hand:\n"
            ret += f"{cards_to_str_52_standard(self.game.best_hand)}\n"
            return ret

        return "You shouldn't be seeing this."
    
    def get_debug_str(self):
        return super().get_debug_str() + self.game.get_debug_str()

     
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

        indi_player_data = PokerPlayer()
        await self.manager.add_player(interaction, indi_player_data)

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

class BetModal(discord.ui.Modal):
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
    def __init__(self, manager, player_count):
        super().__init__()
        self.manager = manager
        self.total_player_count = player_count
        self.active_player_count = player_count
        self.players_with_bets = 0
    
    async def next_player(self, interaction: discord.Interaction):
        """
        Add a player to the bet count, once all players have bet,
        the manager moves to the dealing phase
        """
        self.manager.game.turn_index += 1
        if self.manager.game.turn_index == self.active_player_count:
            self.manager.game.turn_index = 0
            if self.active_player_count == 0:
                self.manager.finalize_game()
            else:
                bet_set = True 
                for player in self.manager.game.player_data:
                    if self.manager.game.player_data[player].active \
                    and self.manager.game.player_data[player].round_bet != self.manager.game.largest_bet:
                        bet_set = False
                if bet_set:
                    if self.manager.game.game_state == 5:
                        self.manager.game.game_state = 6
                    await self.manager.deal_table(interaction)
                next_user = self.manager.game.turn_order[self.manager.game.turn_index]
                if (self.manager.game.player_data[next_user].active) == False:
                    self.next_player()
    
            
    
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
        await interaction.response.send_message(f"Your hand is {cards_to_str_52_standard(current_player.hand)}", ephemeral = True, delete_after = 60)
    
    @discord.ui.button(label = "Call", style = discord.ButtonStyle.green)
    async def call(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Call
        """
        print(f"{interaction.user} pressed {button.label}!")
        await self.manager.make_bet(interaction, self.manager.game.largest_bet)

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
        self.active_player_count -= 1
        self.manager.game.player_data[interaction.user].active = False
        self.manager.base_gui = None
        await interaction.response.send_message(f"{interaction.user.mention} has folded!")



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

def best_hand(user_hand, table):
    """
    This finds the best value using 0-2 of the user_hand
    and 3-5 of the table cards.
    """
    if len(user_hand) != 2:
        raise ValueError("User hand must contain 2 cards")
    if len(table) > 5 or len(table) < 3:
        raise ValueError("Table must contain 3-5 cards")
    
    #During the flop, the card combination is 5 choose 5, so one possible hand per-person
    #During the turn, the card combination is 6 choose 5, so 6 possible hands per-person
    #During the river, the card combination is 7 choose 5, so 21 possible hands per-person
    #Technically, river phase can be sped up here because if a user's best hand is just
    #the five on the table, then they are not winning, they draw at best. Can change if it is slow.
    all_cards = user_hand + table
    card_combinations = list(combinations(all_cards, 5)) # Thank you FoCS for this knowledge :)
    best_value = max([max_hand(list(c)) for c in card_combinations])
    return best_value