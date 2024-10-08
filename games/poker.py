"""Poker game module

Contains all the logic needed to run a game of Texas Hold'em Poker.
It features an closed game model, meaning not all users can interact
with the game at any time, and there is player management.
"""
import random
from itertools import combinations
import discord
from games.game import BaseGame
from games.game import GameManager
from games.game import BasePlayer
from util import double_check
from util import STANDARD_52_DECK
from util import cards_to_str_52_standard
from util import send_info_message
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
        # game state 1 -> accepting players but not playing yet
        super().__init__(game_type=1, player_data={}, game_state=1, cpus=cpus)
        self.deck = generate_deck()
        self.community_cards = []
        self.pool = 0
        self.largest_bet = 0
        self.turn_order = []
        self.active_player_turn_order = []
        self.turn_index = 0
        self.best_hand = []
        self.winner = {}
        random.shuffle(self.deck)

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

class PokerManager(GameManager):
    """
    Represents a manager for a game of poker.
    A brief overview of its attributes and methods:
    Attributes:
    1. game (PokerGame): The game of poker.
    2. base_gui (PokerButtonsBase): The base GUI for the game.
    Methods:
    1. add_player: Adds a player to the game.
    2. remove_player: Removes a player from the game.
    3. start_game: Starts the game.
    4. start_new_round: Starts a new round.
    5. deal_cards: Deals cards to the players.
    6. make_bet: Makes a bet.
    7. deal_table: Deals cards to the table.
    8. finalize_game: Finalizes the game.
    9. get_base_menu_string: Returns a string representation of the base menu.
    10. get_debug_str: Returns a string representation of the manager's debug information.
    """
    def __init__(self, factory, channel, cpus):
        super().__init__(game=PokerGame(cpus), base_gui=PokerButtonsBase(self),
                         channel=channel, factory=factory)

    async def add_player(self, interaction, init_player_data=None):
        """
        Adds a player to the game and updates the turn order if necessary.
        """
        await super().add_player(interaction, init_player_data)
        if interaction.user in self.game.player_data \
        and interaction.user not in self.game.turn_order:
            self.game.turn_order.append(interaction.user)

    async def remove_player(self, interaction):
        """
        Removes a player from the game and updates the turn order if necessary.
        """
        await super().remove_player(interaction)
        if interaction.user not in self.game.player_data \
        and interaction.user in self.game.turn_order:
            self.game.turn_order.remove(interaction.user)
        # if nobody else is left, then quit the game
        if self.game.players == 0:
            await self.quit_game(interaction)

    async def start_game(self, interaction):
        """
        Starts the game.
        """
        if self.game.game_state != 1:
            await send_info_message("This game has already started", interaction)
            return
        # game_state == 4 -> players cannot join or leave
        self.game.game_state = 4
        for player in self.game.turn_order:
            self.game.active_player_turn_order.append(player)

        # swap default GUI to betting phase buttons
        await interaction.channel.send(f"{interaction.user.display_name} started the game!")
        await self.deal_cards(interaction)
        await self.resend(interaction)

    async def start_new_round(self, interaction):
        """
        Reset the game state to player join phase
        """
        self.game.game_state = 1
        active = False
        if len(self.game.active_player_turn_order) != 0:
            active = True

        for player in self.game.turn_order:
            self.game.player_data[player].hand = []
            self.game.player_data[player].round_bet = 0
            self.game.player_data[player].total_bet = 0
            self.game.player_data[player].active = True

        self.game.deck = generate_deck()
        self.game.community_cards = []
        self.game.pool = 0
        self.game.largest_bet = 0
        self.game.active_player_turn_order = []
        self.game.turn_index = 0
        self.game.best_hand = []
        self.game.winner = {}
        random.shuffle(self.game.deck)
        # allow players to join
        self.base_gui = PokerButtonsBase(self)
        if not active:
            await self.resend(interaction)

    async def deal_cards(self, interaction):
        """
        Deal cards to players
        """
        # make sure we're at the end of the betting phase
        if self.game.game_state != 4:
            return
        # game_state 5 -> dealing phase (players cannot join or leave)
        self.game.game_state = 5

        await interaction.channel.send("Dealing cards...")

        # draw 2 cards for every player
        for i in self.game.player_data:
            self.game.player_data[i].hand.extend(STANDARD_52_DECK.draw(2))

        self.base_gui = ButtonsBetPhase(self)

    async def make_bet(self, interaction, bet_amount):
        """
        Set a player's bet
        """
        # checks to see if the game is over
        if await self.game_end_check(interaction):
            return

        # check to see if it is the user's turn
        user = interaction.user
        if self.game.active_player_turn_order[self.game.turn_index] != user:
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
        user_data.round_bet += int(bet_amount)
        user_data.total_bet += int(bet_amount)
        self.game.pool += int(bet_amount)
        user_data.chips -= int(bet_amount)
        if user_data.round_bet >= self.game.largest_bet:
            self.game.largest_bet = user_data.round_bet
        await interaction.channel.send((f"{user.mention} has bet {str(bet_amount)} "
                                        f"chips and now has {str(user_data.chips)} "
                                        "chips left!"))
        await self.base_gui.next_player(interaction, False)
        return

    async def deal_table(self, interaction):
        """
        Deal cards to the table
        """
        self.game.largest_bet = 0
        if len(self.game.community_cards) == 0:
            self.game.community_cards.extend(STANDARD_52_DECK.draw(3))

        elif len(self.game.community_cards) == 5:
            await self.finalize_game(interaction)
        else:
            self.game.community_cards.extend(STANDARD_52_DECK.draw(1))
        await self.resend(interaction)
        return

    async def finalize_game(self, interaction):
        """
        End the game
        """
        self.game.game_state = 7
        self.base_gui = None

        if len(self.game.active_player_turn_order) != 0:
            winning_hand = []
            for player in self.game.player_data:
                if not winning_hand:
                    winning_hand = self.game.player_data[player].hand
                    self.game.winner = player.display_name
                    self.game.best_hand = winning_hand
                else:
                    b_1 = best_hand(winning_hand, self.game.community_cards)
                    b_2 = best_hand(self.game.player_data[player].hand, self.game.community_cards)
                    if b_1 < b_2:
                        winning_hand = self.game.player_data[player].hand
                        self.game.winner = player.display_name
                        self.game.best_hand = winning_hand
            await self.resend(interaction)

        restart_ui = QuitGameButton(self)
        active_msg = await self.channel.send("Play again?", view=restart_ui)
        await restart_ui.wait()
        await active_msg.edit(view=None)
        return

    def get_base_menu_string(self):
        """
        Returns a string representation of the base menu.
        """
        if self.game.game_state == 1:
            return "Who's ready for a game of poker?"

        if self.game.game_state == 4:
            ret = "Current bets and chips:\n"
            for player in self.game.turn_order:
                player_data = self.game.player_data[player]
                ret += f"{player.display_name}: {player_data.get_bet_phase_str()}\n"
            return ret

        if self.game.game_state == 5:
            ret = "Largest bet:\n"
            ret += f"{self.game.largest_bet}\n"
            ret += "Pool:\n"
            ret += f"{self.game.pool}\n"
            who_turn = self.game.active_player_turn_order[self.game.turn_index].mention
            ret += f"It's {who_turn}'s turn to bet!\n"
            return ret

        if self.game.game_state == 6:
            ret = "Community cards:\n"
            ret += f"{cards_to_str_52_standard(self.game.community_cards)}\n"
            ret += "Largest bet:\n"
            ret += f"{self.game.largest_bet}\n"
            ret += "Pool:\n"
            ret += f"{self.game.pool}\n"
            return ret

        if self.game.game_state == 7:
            ret = f"{self.game.winner} has WON!\n"
            ret += "Winning hand:\n"
            ret += f"{cards_to_str_52_standard(self.game.best_hand)}\n"
            if len(self.game.active_player_turn_order) <= 0:
                ret = ""
            return ret

        return "You shouldn't be seeing this."

    def get_debug_str(self):
        return super().get_debug_str() + self.game.get_debug_str()


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


class ButtonsBetPhase(discord.ui.View):
    """
    Button set that allows players to bet
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.disabled_view = None

    async def next_player(self, interaction: discord.Interaction, folded):
        """
        Add a player to the bet count, once all players have bet,
        the manager moves to the dealing phase
        """
        if not folded:
            self.manager.game.turn_index += 1
        if self.manager.game.turn_index >= len(self.manager.game.active_player_turn_order):
            self.manager.game.turn_index = 0
            if len(self.manager.game.active_player_turn_order) == 0:
                await self.manager.finalize_game(interaction)
            else:
                bet_set = True
                for player in self.manager.game.player_data:
                    if self.manager.game.player_data[player].active \
                    and (self.manager.game.player_data[player].round_bet !=
                        self.manager.game.largest_bet):
                        bet_set = False
                if bet_set:
                    if self.manager.game.game_state == 5:
                        self.manager.game.game_state = 6
                    for player in self.manager.game.turn_order:
                        self.manager.game.player_data[player].round_bet = 0
                    await self.manager.deal_table(interaction)


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
    hand.sort(key = lambda x: lookup.index(x.value))
    same_suit = True
    for c in hand:
        if c.name != hand[0].name:
            same_suit = False
            break
    highest_value = lookup.index(hand[4].value)

    #Check Royal Flush
    if same_suit:
        if (hand[0].value == "10" and hand[1].value == "J"
            and hand[2].value == "Q" and hand[3].value == "K" and hand[4].value == "A"):
            return encode_hand_value((10, highest_value))

    #Check Straight Flush
    if same_suit:
        #Straight Flush uses alt_lookup because if it is not a Royal Flush, A=1 if it is a Flush
        is_straight = True
        for index in range(4):
            if alt_lookup.index(hand[index].value) + 1 != alt_lookup.index(hand[index + 1].value):
                is_straight = False
                break
        if is_straight:
            return encode_hand_value((9, highest_value))

    type_dict = dict()
    for c in hand:
        type_dict[c.value] = type_dict.get(c.value, 0) + 1

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
        return encode_hand_value((6, )
        + tuple(sorted([lookup.index(c.value) for c in hand], reverse = True)))

    #Check Straight
    is_high_straight = True
    for index in range(4):
        if lookup.index(hand[index].value) + 1 != lookup.index(hand[index + 1].value):
            is_high_straight = False
            break
    is_low_straight = True
    for index in range(4):
        if alt_lookup.index(hand[index].value) + 1 != alt_lookup.index(hand[index + 1].value):
            is_low_straight = False
            break
    if is_high_straight:
        return encode_hand_value((5, highest_value))
    if is_low_straight:
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
    return encode_hand_value((1, )
    + tuple(sorted([lookup.index(c.value) for c in hand], reverse = True)))

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
