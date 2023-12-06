"""Blackjack game module

Contains all the logic needed to run a game of Blackjack.
It features an closed game model, meaning not all users can interact
with the game at any time, and there is player management.
"""
import logging
import discord
from games.game import BaseGame
from games.game import GameManager
from games.game import BasePlayer
from util import double_check
from util import STANDARD_52_DECK
from util import cards_to_str_52_standard
from util import send_info_message


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


class BlackjackManager(GameManager):
    """
    Blackjack manager class
    """
    def __init__(self, factory, channel):
        super().__init__(game=BlackjackGame(), base_gui=BlackjackButtonsBase(self),
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
        """
        Start the game
        """
        self.quick_log("Starting game", interaction)
        if self.game.game_state != 1:
            self.quick_log("Game didn't start (already started)")
            await send_info_message("This game has already started", interaction)
            return
        # game_state == 4 -> players cannot join or leave
        self.game.game_state = 4
        # swap default GUI to betting phase buttons
        await interaction.channel.send(f"{interaction.user.display_name} started the game!")
        self.base_gui = ButtonsBetPhase(self)
        await self.resend(interaction)

    async def start_new_round(self, interaction):
        """
        Reset the game state to player join phase
        """
        for player in self.game.turn_order:
            self.game.player_data[player].reset()
        self.game.dealer_hand.clear()
        self.game.dealer_hidden_card = None
        self.game.turn_index = -1
        self.game.game_state = 1
        # allow players to join
        self.base_gui = BlackjackButtonsBase(self)
        await self.resend(interaction)

    async def deal_cards(self):
        """
        Deals cards to all players, used once betting is done
        """
        # make sure we're at the end of the betting phase
        if self.game.game_state != 4:
            return
        # game_state 5 -> dealing phase (players cannot join or leave)
        self.game.game_state = 5

        await self.channel.send("All players have bet! Dealing cards...")

        # draw 2 cards for the dealer and every player
        self.game.dealer_hand.extend(STANDARD_52_DECK.draw(1))
        # the dealer's hidden card is stored seperately
        hidden_card = STANDARD_52_DECK.draw(1)[0]
        self.game.dealer_hidden_card = hidden_card
        for i in self.game.player_data:
            self.game.player_data[i].hand.extend(STANDARD_52_DECK.draw(2))

        # check to see if the dealer got a natural 21 and add the
        # hidden card to its normal hand if so (so it shows up in
        # the base menu)
        dealer_card = self.game.dealer_hand[0]
        if (dealer_card.value == "A" and hidden_card.value in ("J", "Q", "K") or
            hidden_card.value == "A" and dealer_card.value in ("J", "Q", "K")
        ):
            self.game.dealer_hidden_card = None
            self.game.dealer_hand.append(hidden_card)

        # TODO: resend doesn't support sending only based on channel.
        # current solution is to just reimplement its logic here,
        # pls improve
        if  self.game.game_state == -1:
            return
        await self.current_active_menu.edit(view=None)
        # if dealer's hidden card is None, that means we added it to
        # its hand because it got blackjack
        if self.game.dealer_hidden_card is None:
            self.current_active_menu = await self.channel.send(self.get_base_menu_string(),
                                                               view=None, silent=True)
            self.channel.send("Dealer got blackjack! House wins!")
            # move straight to payout phase
            self.make_payout(21)
        else:
            # otherwise initiate play phase
            self.base_gui = BlackjackButtonsBaseGame(self)
            self.current_active_menu = await self.channel.send(self.get_base_menu_string(),
                                                               view=self.base_gui, silent=True)
            await self.start_next_player_turn()

    async def start_next_player_turn(self):
        """
        Start the next player's turn
        """
        self.game.turn_index += 1
        # if we made it to the end of the list, have the dealer go
        if self.game.turn_index == self.game.players:
            await self.channel.send("All players have had their turn, starting dealer draw!")
            self.game.game_state = 6
            await self.dealer_draw()
            return

        # retrieving data
        active_player = self.game.get_active_player()
        active_player_data = self.game.player_data[active_player]
        active_player_hand = active_player_data.hand

        (eleven_aces, value) = bj_add(active_player_hand)
        # if the player got a blackjack, skip their turn and give them
        # a 2.5x payout immediately
        if value == 21:
            await self.channel.send(f"{active_player.mention} got blackjack! Moving on...")
            active_player_data.current_payout_multiplier = 2.5
            await self.start_next_player_turn()
            return
        active_player_data.hand_value = value
        active_player_data.eleven_ace_count = eleven_aces

        # initiate the hit or stand menu
        hit_me_view = HitOrStand(self, active_player)
        active_msg = await self.channel.send((f"{active_player.mention}, your turn! Your hand is\n"
                                        f"{cards_to_str_52_standard(active_player_hand)}\n"
                                        "What would you like to do?"), view = hit_me_view)
        # wait for the user to press hit or stand, then remove the
        # buttons from the menu once they do
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

    async def hit_user(self, interaction):
        """
        Adds a card to the user's hand, and handles any consequences
        """
        # check to make sure the game hasn't ended, do nothing if it has
        if await self.game_end_check(interaction):
            return

        # check to make sure they're in the game
        if interaction.user not in self.game.player_data:
            await send_info_message("You are not in this game.", interaction)
            return

        # note: we don't check to see if this is the player's turn,
        # so ensure that check is done before we get here
        active_player = interaction.user
        active_player_data = self.game.player_data[interaction.user]
        new_card = STANDARD_52_DECK.draw(1)[0]
        active_player_data.hand.append(new_card)
        response_message = f"{active_player.mention} drew {cards_to_str_52_standard([new_card])}! "

        # manage add the card's value to the player's hand
        if new_card.value == "A":
            active_player_data.hand_value += 11
            active_player_data.eleven_ace_count += 1
        elif new_card.value in ("J", "Q", "K"):
            active_player_data.hand_value += 10
        else:
            active_player_data.hand_value += int(new_card.value)

        # reduce the value of any aces while the user is above 21,
        # and if they are still above 21 when all aces are reduced,
        # declare that they're gone bust
        while active_player_data.hand_value > 21:
            if active_player_data.eleven_ace_count > 0:
                active_player_data.hand_value -= 10
                active_player_data.eleven_ace_count -= 1
            else:
                # if the user busts, we set their payout to 0, which
                # is never overwritten even if the dealer busts too
                response_message += "That's a bust!"
                active_player_data.current_payout_multiplier = 0
                await interaction.response.send_message(response_message)
                await self.start_next_player_turn()
                return

        if active_player_data.hand_value == 21:
            response_message += "That's 21!"
            await interaction.response.send_message(response_message)
            await self.start_next_player_turn()
            return

        # alert players of the new draw and allow them to go again
        response_message += (f"\nTheir hand is now "
                             f"{cards_to_str_52_standard(active_player_data.hand)}, "
                             f"which has a max value of {active_player_data.hand_value}! ")
        response_message += "What next?"
        hit_me_view = HitOrStand(self, active_player)
        active_msg = await self.channel.send(response_message, view=hit_me_view)
        # wait for the buttons to be pressed and remove once one has
        await hit_me_view.wait()
        await active_msg.edit(view=None)

    async def make_bet(self, interaction, bet_amount):
        """
        Set a player's bet
        """
        # checks to see if the game is over
        if await self.game_end_check(interaction):
            return

        # check to see if the user can bet, and deny them if not
        user = interaction.user
        user_data = self.game.player_data[user]
        if user_data.current_bet != 0:
            await send_info_message("You've already bet this round.", interaction)
            return
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
        user_data.current_bet = int(bet_amount)
        user_data.chips -= int(bet_amount)
        await interaction.channel.send((f"{user.mention} has bet {str(bet_amount)} "
                                        f"chips and now has {str(user_data.chips)} "
                                        "chips left!"))
        self.game.betted_players += 1
        if self.game.players == self.game.betted_players:
            await self.deal_cards()
        return

    async def dealer_draw(self):
        """
        Perform the dealer's play
        """
        # reveal the dealer's hidden card if it hasn't been already
        # note: this check is probably worthless since the only case in
        # which it isn't hidden skips this phase
        if self.game.dealer_hidden_card is not None:
            await self.channel.send((f"Dealer's hidden card is "
                               f"{cards_to_str_52_standard([self.game.dealer_hidden_card])}!"))
            self.game.dealer_hand.append(self.game.dealer_hidden_card)
            self.game.dealer_hidden_card = None

        (_, hand_value) = bj_add(self.game.dealer_hand)
        await self.channel.send((f"Dealer's hand is "
                                    f"{cards_to_str_52_standard(self.game.dealer_hand)}, "
                                    f"which has a total value of {hand_value}!"))

        # keep drawing until the deal exceeds 17 cards (bust or not)
        while hand_value < 17:
            new_card = STANDARD_52_DECK.draw(1)
            await self.channel.send(f"Dealer drew {cards_to_str_52_standard(new_card)}!")
            new_card = new_card[0]
            self.game.dealer_hand.append(new_card)
            if new_card.value == "A":
                # dealer always treats new aces as 11 unless doing so
                # results in a bust
                if hand_value + 11 > 21:
                    hand_value += 1
                else:
                    hand_value += 11
            elif new_card.value in ("J", "Q", "K"):
                hand_value += 10
            else:
                hand_value += int(new_card.value)

            await self.channel.send((f"Dealer's hand is "
                                     f"{cards_to_str_52_standard(self.game.dealer_hand)}, "
                                     f"which has a total value of {hand_value}!"))

        # treat dealer's hand as 0 if it busts (so any non-busted
        # player is treated as winning)
        if hand_value > 21:
            await self.channel.send("Dealer bust!")
            hand_value = 0

        await self.make_payout(hand_value)

    async def make_payout(self, dealer_hand_value):
        """
        Check through game player list, compare it to the dealer's hand
        value, and make payment accordingly
        """
        payout_str = "Game payouts:"
        for player in self.game.turn_order:
            player_data = self.game.player_data[player]
            # if the payout multiplier is 1, then the user hasn't had
            # its payment determined yet through bust or blackjack, so
            # we need to compare it to the dealer's hand
            if player_data.current_payout_multiplier == 1:
                if player_data.hand_value > dealer_hand_value:
                    player_data.current_payout_multiplier = 2
                elif player_data.hand_value < dealer_hand_value:
                    player_data.current_payout_multiplier = 0
            payout_str = payout_str + f"\n{player.display_name}: " + player_data.get_payout_str()
            player_data.chips += round(player_data.current_bet
                                       * player_data.current_payout_multiplier)

        await self.channel.send(payout_str)

        # then initiate the endgame phase
        self.game.game_state = 7
        restart_ui = QuitGameButton(self)
        active_msg = await self.channel.send("Play again?", view=restart_ui)
        await restart_ui.wait()
        await active_msg.edit(view=None)


class QuitGameButton(discord.ui.View):
    """
    Button set that asks players if they want to play the game again
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

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


class BlackjackButtonsBase(discord.ui.View):
    """
    Initial "join game" buttons
    """
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

        indi_player_data = BlackjackPlayer()
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


class BlackjackButtonsBaseGame(discord.ui.View):
    """
    Literally just a resend button
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    @discord.ui.button(label = "Resend", style = discord.ButtonStyle.gray)
    async def resend(self, interaction: discord.Interaction, button: discord.ui.Button):
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
    Contains the popup box that shows when players make their bets
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
    Contains the "bet" button and also keeps track of players who have
    placed bets
    """
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    @discord.ui.button(label = "Bet!", style = discord.ButtonStyle.green)
    async def bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Allows the user to bring up the betting menu
        """
        print(f"{interaction.user} pressed {button.label}!")
        if not await self.manager.deny_non_participants(interaction):
            return
        await interaction.response.send_modal(BetModal(self.manager))


class HitOrStand(discord.ui.View):
    """
    Contains the "hit" and "stand" buttons when it's a certain player's
    turn. Keeps track of which player's turn it is and denies input
    to other players
    """
    def __init__(self, manager, active_player):
        super().__init__()
        self.manager = manager
        self.active_player = active_player

    @discord.ui.button(label = "Hit Me!", style = discord.ButtonStyle.green)
    async def hit_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Check if the interaction is valid, and if so, call hit_user
        """
        print(f"{interaction.user} pressed {button.label}!")
        if interaction.user != self.active_player:
            await send_info_message("It's not your turn.", interaction)
            return
        # stop accepting interactions for this message
        self.stop()
        await self.manager.hit_user(interaction)

    @discord.ui.button(label = "Stand", style = discord.ButtonStyle.blurple)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Check if the interaction is valid, and if so, make the user stand
        and start the next player's turn
        """
        if interaction.user != self.active_player:
            await send_info_message("It's not your turn.", interaction)
            return
        print(f"{interaction.user} pressed {button.label}!")
        await interaction.response.send_message(f"{self.active_player.display_name} is standing!")
        # stop accepting interactions for this message
        self.stop()
        await self.manager.start_next_player_turn()


def bj_add(cards):
    """
    cards is a list of Card objects
    returns a tuple containing the number of aces that are counted as
    eleven, and the value of the hand
    """
    total = 0
    ace_count = 0
    faces = ('A', 'J', 'Q', 'K')
    for card in cards:
        if card.value not in faces:
            total += int(card.value)
        elif card.value in faces[1:]:
            total += 10
        else:
            ace_count += 1
    total += 11 * ace_count
    ret_ace_count = ace_count
    for _ in range(ace_count):
        if total > 21:
            ret_ace_count -= 1
            total -= 10
        else:
            break
    return (ret_ace_count, total)
