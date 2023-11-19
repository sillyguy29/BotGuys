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
        await self.deal_cards()

    async def start_new_round(self, interaction):
        for player in self.game.turn_order:
            self.game.player_data[player].reset()
        self.game.dealer_hand.clear()
        self.game.dealer_hidden_card = None
        self.game.player_turn = -1
        self.game.game_state = 1
        self.base_gui = BlackjackButtonsBase(self)
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
        await self.resend(interaction)

    async def start_next_player_turn(self):
        self.game.player_turn += 1
        if self.game.player_turn == self.game.players:
            await self.channel.send("All players have had their turn, starting dealer draw!")
            self.game.game_state = 6
            await self.dealer_draw()
            return

        active_player = self.game.get_active_player()
        active_player_data = self.game.player_data[active_player]
        active_player_hand = active_player_data.hand

        (eleven_aces, value) = bj_add(active_player_hand)
        if value == 21:
            await self.channel.send(f"{active_player.mention} got blackjack! Moving on...")
            active_player_data.current_payout_multiplier = 2.5
            await self.start_next_player_turn()
            return
        active_player_data.hand_value = value
        active_player_data.eleven_ace_count = eleven_aces

        hit_me_view = HitOrStand(self, active_player)
        active_msg = await self.channel.send((f"{active_player.mention}, your turn! Your hand is\n"
                                        f"{cards_to_str_52_standard(active_player_hand)}\n"
                                        "What would you like to do?"), view = hit_me_view)
        await hit_me_view.wait()
        await active_msg.edit(view=None)

    def get_base_menu_string(self):
        if self.game.game_state == 1:
            return "Who's ready for a game of blackjack?"

        elif self.game.game_state == 4:
            ret = "Current bets and chips:\n"
            for player in self.game.turn_order:
                player_data = self.game.player_data[player]
                ret += f"{player.display_name}: {player_data.get_bet_phase_str()}\n"
            return ret

        elif self.game.game_state == 5:
            ret = f"Dealer hand: {cards_to_str_52_standard(self.game.dealer_hand)}"
            # no hidden card means we added it to the dealer's hand
            if self.game.dealer_hidden_card is not None:
                ret += ", ??"
            for player in self.game.turn_order:
                player_data = self.game.player_data[player]
                ret += f"\n{player.mention} {player_data.get_play_phase_str()}"
            return ret

        return "You shouldn't be seeing this."

     
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
        self.player_count = player_count
        self.players_with_bets = 0

    async def add_betted_player(self):
        self.players_with_bets += 1
        if self.players_with_bets == self.player_count:
            await self.manager.deal_cards()

    @discord.ui.button(label = "Bet!", style = discord.ButtonStyle.green)
    async def bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Allows the user to bring up the betting menu
        """
        print(f"{interaction.user} pressed {button.label}!")
        if not await self.manager.deny_non_participants(interaction):
            return
        await interaction.response.send_modal(BetModal(self.manager))

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