# discord_bot.py (With configurable total players from 3 to 6)
import os
import sys
import asyncio
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from src.engine.card import Card, CardType, Suit
from src.engine.deck import Deck
from src.engine.rules import get_legal_plays
from src.engine.state import GameState
from src.agents.random_agent import RandomAgent
from src.agents.heuristic_agent import HeuristicAgent

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

games = {}

# --- VISUAL HELPERS ---

SUIT_EMOJIS = {
    Suit.RED: "🟥",
    Suit.BLUE: "🟦",
    Suit.GREEN: "🟩",
    Suit.YELLOW: "🟨",
}

def format_card(card: Card) -> str:
    if card.card_type == CardType.WIZARD:
        return "🧙 **Wizard**"
    if card.card_type == CardType.JESTER:
        return "🃏 **Jester**"
    emoji = SUIT_EMOJIS.get(card.suit, "🎴")
    return f"{emoji} **{card.suit.name.capitalize()} {card.value}**"

def format_hand(hand: list[Card]) -> str:
    return " | ".join([format_card(c) for c in hand]) if hand else "*Empty*"

def format_trick_table(trick: list[tuple[int, Card]], players: list) -> str:
    if not trick:
        return "*No cards played yet*"
    return "\n".join([f"• **{players[p].display_name}**: {format_card(c)}" for p, c in trick])

def sort_hand(hand: list[Card]) -> list[Card]:
    suit_order = {Suit.BLUE: 1, Suit.GREEN: 2, Suit.RED: 3, Suit.YELLOW: 4}
    
    def card_sort_key(card: Card):
        if card.card_type == CardType.WIZARD:
            return (2, 0, 0)
        elif card.card_type == CardType.JESTER:
            return (3, 0, 0)
        else:
            s_val = suit_order.get(card.suit, 5)
            return (1, s_val, card.value)
            
    return sorted(hand, key=card_sort_key)


class BotPlayer:
    def __init__(self, name: str, agent):
        self.display_name = name
        self.mention = f"🤖 **{name}**"
        self.agent = agent
        self.is_bot = True

    async def send(self, *args, **kwargs):
        pass


# --- UI INTERACTIVE VIEWS ---

class BidSelectView(discord.ui.View):
    def __init__(self, max_bid: int, future_result, current_bids: dict, round_number: int, is_last_bidder: bool, enable_restriction: bool):
        super().__init__(timeout=120)
        self.future_result = future_result

        forbidden_bid = None
        if enable_restriction and is_last_bidder:
            sum_so_far = sum(current_bids.values())
            forbidden_bid = round_number - sum_so_far

        for b in range(max_bid + 1):
            is_disabled = (b == forbidden_bid)
            
            if is_disabled:
                style = discord.ButtonStyle.danger
                label = f"Bid {b} (Forbidden)"
            elif b == 0:
                style = discord.ButtonStyle.secondary
                label = f"Bid {b}"
            else:
                style = discord.ButtonStyle.primary
                label = f"Bid {b}"

            row_idx = b // 5
            button = discord.ui.Button(
                label=label,
                style=style,
                disabled=is_disabled,
                custom_id=f"bid_{b}",
                row=min(row_idx, 4)
            )
            button.callback = self.make_callback(b, is_disabled)
            self.add_item(button)

    def make_callback(self, bid_val: int, is_disabled: bool):
        async def callback(interaction: discord.Interaction):
            if is_disabled:
                await interaction.response.send_message("❌ This bid is illegal because total bids cannot equal the round tricks!", ephemeral=True)
                return
            await interaction.response.defer()
            self.stop()
            if not self.future_result.done():
                self.future_result.set_result(bid_val)
        return callback


class CardSelectView(discord.ui.View):
    def __init__(self, hand: list[Card], playable: list[Card], future_result):
        super().__init__(timeout=120)
        self.future_result = future_result

        suit_styles = {
            Suit.RED: discord.ButtonStyle.danger,
            Suit.BLUE: discord.ButtonStyle.primary,
            Suit.GREEN: discord.ButtonStyle.success,
            Suit.YELLOW: discord.ButtonStyle.secondary,
        }

        for idx, card in enumerate(hand):
            is_disabled = card not in playable
            row_idx = idx // 5

            if card.card_type == CardType.WIZARD:
                label = "Wizard"
                emoji = "🧙"
                style = discord.ButtonStyle.success if not is_disabled else discord.ButtonStyle.secondary
            elif card.card_type == CardType.JESTER:
                label = "Jester"
                emoji = "🃏"
                style = discord.ButtonStyle.secondary
            else:
                label = f"{card.suit.name.capitalize()} {card.value}"
                emoji = SUIT_EMOJIS.get(card.suit, "🎴")
                style = suit_styles.get(card.suit, discord.ButtonStyle.primary) if not is_disabled else discord.ButtonStyle.secondary

            button = discord.ui.Button(
                label=label,
                emoji=emoji,
                style=style,
                disabled=is_disabled,
                custom_id=f"card_{idx}",
                row=min(row_idx, 4)
            )
            button.callback = self.make_callback(card)
            self.add_item(button)

    def make_callback(self, card: Card):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer()
            self.stop()
            if not self.future_result.done():
                self.future_result.set_result(card)
        return callback


class TrumpSelectView(discord.ui.View):
    def __init__(self, future_result):
        super().__init__(timeout=120)
        self.future_result = future_result

        suit_styles = {
            Suit.RED: discord.ButtonStyle.danger,
            Suit.BLUE: discord.ButtonStyle.primary,
            Suit.GREEN: discord.ButtonStyle.success,
            Suit.YELLOW: discord.ButtonStyle.secondary,
        }

        for suit in Suit:
            button = discord.ui.Button(
                label=suit.name.capitalize(),
                emoji=SUIT_EMOJIS[suit],
                style=suit_styles.get(suit, discord.ButtonStyle.primary),
            )
            button.callback = self.make_callback(suit)
            self.add_item(button)

    def make_callback(self, suit: Suit):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer()
            self.stop()
            if not self.future_result.done():
                self.future_result.set_result(suit)
        return callback


# --- GAME CONTROLLER ---

class DiscordWizardGame:
    def __init__(self, channel: discord.TextChannel, players: list, num_rounds: Optional[int] = None,
                 enable_bid_restriction: bool = True, blind_round_one: bool = True):
        self.channel = channel
        self.players = players
        self.num_players = len(players)
        self.num_rounds = num_rounds
        self.enable_bid_restriction = enable_bid_restriction
        self.blind_round_one = blind_round_one
        self.state = GameState(num_players=self.num_players, round_number=1)
        self.deck = Deck()
        self.dm_messages = {}

    async def render_and_update(self, player_id: int, embed: discord.Embed, view: discord.ui.View = None):
        p = self.players[player_id]
        if getattr(p, "is_bot", False):
            return

        try:
            if player_id in self.dm_messages:
                await self.dm_messages[player_id].edit(embed=embed, view=view)
            else:
                msg = await p.send(embed=embed, view=view)
                self.dm_messages[player_id] = msg
        except discord.Forbidden:
            pass

    async def update_all_boards(self, title: str, active_turn: int = None, view_p_id: int = None, view: discord.ui.View = None, completed_trick: list = None):
        active_trump_suit = getattr(self.state, "trump_suit", None)
        if not active_trump_suit and self.state.trump_card:
            if self.state.trump_card.card_type not in (CardType.WIZARD, CardType.JESTER):
                active_trump_suit = self.state.trump_card.suit

        if active_trump_suit:
            trump_str = f"{SUIT_EMOJIS[active_trump_suit]} **{active_trump_suit.name.capitalize()}**"
        else:
            trump_str = "None (No Trump / Jester)"

        if self.state.lead_suit:
            lead_str = f"{SUIT_EMOJIS[self.state.lead_suit]} **{self.state.lead_suit.name.capitalize()}**"
        else:
            lead_str = "None (No Lead / Wizard / Jester)"

        lead_player_id = (self.state.dealer_id + 1) % self.num_players
        ordered_player_ids = [(lead_player_id + offset) % self.num_players for offset in range(self.num_players)]

        for p_id, p in enumerate(self.players):
            if getattr(p, "is_bot", False):
                continue

            embed = discord.Embed(title=title, color=discord.Color.blue())
            
            embed.add_field(name="Dealer", value=self.players[self.state.dealer_id].display_name, inline=True)
            embed.add_field(name="Trump Card", value=format_card(self.state.trump_card) if self.state.trump_card else "None", inline=True)
            embed.add_field(name="Active Trump", value=trump_str, inline=True)
            embed.add_field(name="🎯 Lead Suit", value=lead_str, inline=False)

            if self.blind_round_one and self.state.round_number == 1:
                embed.add_field(name="🎴 Your Hand", value="🔒 *Hidden (Round 1 Blind Variant)*", inline=False)
                
                others_hands = []
                for other_id in ordered_player_ids:
                    if other_id != p_id:
                        other_hand_str = format_hand(self.state.hands.get(other_id, []))
                        others_hands.append(f"• **{self.players[other_id].display_name}**: {other_hand_str}")
                embed.add_field(name="👀 Other Players' Hands", value="\n".join(others_hands), inline=False)
            else:
                hand_str = format_hand(self.state.hands.get(p_id, []))
                embed.add_field(name="🎴 Your Hand", value=hand_str, inline=False)

            active_table = completed_trick if completed_trick is not None else self.state.current_trick
            embed.add_field(name="⚔️ Table Cards", value=format_trick_table(active_table, self.players), inline=False)

            bids_list = []
            for i in ordered_player_ids:
                bid_val = self.state.bids.get(i) if isinstance(self.state.bids, dict) else (self.state.bids[i] if i < len(self.state.bids) else None)
                won_val = self.state.tricks_won.get(i, 0) if isinstance(self.state.tricks_won, dict) else (self.state.tricks_won[i] if i < len(self.state.tricks_won) else 0)
                
                bid_disp = f"`{bid_val}`" if bid_val is not None else "`-`"
                lead_tag = " 🚩 *(Leads Round)*" if i == lead_player_id else ""
                
                bids_list.append(f"• **{self.players[i].display_name}**{lead_tag}: Bid {bid_disp} | Won `{won_val}`")

            embed.add_field(name="📊 Scoreboard & Bids (Play Order)", value="\n".join(bids_list), inline=False)

            if active_turn is not None:
                turn_str = f"👉 **YOUR TURN!**" if active_turn == p_id else f"⏳ Waiting for **{self.players[active_turn].display_name}**..."
                embed.add_field(name="Turn Status", value=turn_str, inline=False)

            attach_view = view if (p_id == view_p_id) else None
            await self.render_and_update(p_id, embed, attach_view)

    async def start(self):
        max_possible_rounds = 60 // self.num_players

        if self.num_rounds is not None and self.num_rounds > 0:
            total_rounds = min(self.num_rounds, max_possible_rounds)
        else:
            total_rounds = max_possible_rounds

        for round_num in range(1, total_rounds + 1):
            self.state.round_number = round_num
            starting_p = (self.state.dealer_id + 1) % self.num_players
            self.dm_messages.clear()

            self.deck.reset()
            self.deck.shuffle()
            temp_hands, temp_trump = self.deck.deal(self.num_players, round_num)
            
            self.state.hands = {p_id: sort_hand(h) for p_id, h in temp_hands.items()}
            self.state.trump_card = temp_trump
            
            if temp_trump:
                if temp_trump.card_type == CardType.WIZARD:
                    dealer_user = self.players[self.state.dealer_id]
                    dealer_choice = await self.prompt_trump_choice(dealer_user, self.state.dealer_id)
                    self.state.trump_suit = dealer_choice
                elif temp_trump.card_type == CardType.JESTER:
                    self.state.trump_suit = None
                else:
                    self.state.trump_suit = temp_trump.suit
            else:
                self.state.trump_suit = None

            if temp_trump and temp_trump.card_type not in (CardType.WIZARD, CardType.JESTER):
                self.state.trump_suit = temp_trump.suit

            self.state.lead_suit = None
            self.state.current_trick = []
            self.state.last_trick = []
            self.state.tricks_won = {i: 0 for i in range(self.num_players)}
            self.state.bids = {}
            self.state.current_player = starting_p

            await self.update_all_boards(title=f"🎯 Bidding Phase — Round {round_num}")

            for bid_idx in range(self.num_players):
                curr_p = self.state.current_player
                player_user = self.players[curr_p]
                is_last = (bid_idx == self.num_players - 1)
                
                await self.update_all_boards(title=f"🎯 Bidding Phase — Round {round_num}", active_turn=curr_p)
                
                bid = await self.prompt_bid(player_user, curr_p, round_num, is_last)
                self.state.record_bid(curr_p, bid)
                
                await self.update_all_boards(title=f"🎯 Bidding Phase — Round {round_num}")
                
                self.state.current_player = (self.state.current_player + 1) % self.num_players

            self.state.current_player = starting_p

            for trick_num in range(round_num):
                for _ in range(self.num_players):
                    curr_p = self.state.current_player
                    user = self.players[curr_p]
                    
                    hand = self.state.hands[curr_p]
                    playable = get_legal_plays(hand, self.state.lead_suit)
                    
                    await self.update_all_boards(title=f"⚔️ Round {round_num} | Trick {trick_num + 1}/{round_num}", active_turn=curr_p)

                    card = await self.prompt_card_play(user, curr_p, hand, playable, round_num, trick_num)
                    winner = self.state.play_card(curr_p, card)
                    
                    await self.update_all_boards(title=f"⚔️ Round {round_num} | Trick {trick_num + 1}/{round_num}")

                    if winner is not None:
                        completed_trick_cards = list(self.state.last_trick)
                        await self.update_all_boards(
                            title=f"🏆 {self.players[winner].display_name} WON Trick {trick_num + 1}!",
                            completed_trick=completed_trick_cards
                        )
                        await asyncio.sleep(4.0)

            round_pts = self.state.calculate_round_scores()
            score_embed = discord.Embed(title=f"📊 Round {round_num}/{total_rounds} Complete!", color=discord.Color.green())
            for p_id in range(self.num_players):
                u = self.players[p_id]
                score_embed.add_field(
                    name=u.display_name,
                    value=f"Bid: `{self.state.bids[p_id]}` | Won: `{self.state.tricks_won[p_id]}`\nPts: `{round_pts[p_id]}` | Total: **{self.state.scores[p_id]}**",
                    inline=True
                )
            
            for p_id in range(self.num_players):
                await self.render_and_update(p_id, score_embed)
            
            await asyncio.sleep(3.0)
            self.state.dealer_id = (self.state.dealer_id + 1) % self.num_players

        final_embed = discord.Embed(title="🎉 GAME OVER - Final Results", color=discord.Color.purple())
        for p_id in range(self.num_players):
            final_embed.add_field(name=self.players[p_id].display_name, value=f"**{self.state.scores[p_id]}** pts", inline=True)
            
        for p_id in range(self.num_players):
            await self.render_and_update(p_id, final_embed)
        await self.channel.send(embed=final_embed)

    async def prompt_bid(self, user, player_id: int, round_num: int, is_last_bidder: bool) -> int:
        forbidden_bid = None
        if self.enable_bid_restriction and is_last_bidder:
            sum_so_far = sum(self.state.bids.values())
            forbidden_bid = round_num - sum_so_far

        if getattr(user, "is_bot", False):
            await asyncio.sleep(0.8)
            if hasattr(user.agent, "select_bid") and "forbidden_bid" in user.agent.select_bid.__code__.co_varnames:
                return user.agent.select_bid(self.state, player_id, forbidden_bid=forbidden_bid)
            return user.agent.select_bid(self.state, player_id)

        loop = asyncio.get_event_loop()
        future = loop.create_future()
        view = BidSelectView(round_num, future, self.state.bids, round_num, is_last_bidder, self.enable_bid_restriction)

        await self.update_all_boards(
            title=f"🎯 Bidding Phase — Round {self.state.round_number}",
            active_turn=player_id,
            view_p_id=player_id,
            view=view
        )
        return await future

    async def prompt_card_play(self, user, player_id: int, hand: list[Card], playable: list[Card], round_num: int, trick_num: int) -> Card:
        if getattr(user, "is_bot", False):
            await asyncio.sleep(1.0)
            return user.agent.select_card(self.state, player_id)

        loop = asyncio.get_event_loop()
        future = loop.create_future()
        view = CardSelectView(hand, playable, future)

        await self.update_all_boards(
            title=f"⚔️ Round {round_num} | Trick {trick_num + 1}/{round_num}",
            active_turn=player_id,
            view_p_id=player_id,
            view=view
        )
        return await future

    async def prompt_trump_choice(self, dealer_user, dealer_id: int) -> Suit:
        if getattr(dealer_user, "is_bot", False):
            return dealer_user.agent.select_trump(self.state, dealer_id)

        loop = asyncio.get_event_loop()
        future = loop.create_future()
        view = TrumpSelectView(future)

        embed = discord.Embed(title="🧙 Wizard Turned! Pick Trump Suit", color=discord.Color.gold())
        
        hand_str = "🔒 *Hidden (Round 1 Blind Variant)*" if (self.blind_round_one and self.state.round_number == 1) else format_hand(self.state.hands.get(dealer_id, []))
        embed.add_field(name="🎴 Your Hand", value=hand_str, inline=False)

        await self.render_and_update(dealer_id, embed, view)
        trump_suit = await future

        self.state.trump_suit = trump_suit
        await self.update_all_boards(title=f"🎯 Bidding Phase — Round {self.state.round_number}")
        
        return trump_suit


# --- SLASH COMMANDS ---

@bot.tree.command(name="start_wizard", description="Start a Wizard game lobby in this channel")
@app_commands.describe(
    rounds="Optional custom round count (defaults to max rounds)",
    total_players="Total number of players in the game (3 to 6, default 3)",
    bid_restriction="Prevent total bids from matching round tricks (default True)",
    blind_round_one="Hide your hand in round 1 (default True)",
    bot_type="Choose AI type for empty slots (heuristic or random)"
)
@app_commands.choices(bot_type=[
    app_commands.Choice(name="Heuristic (Smart)", value="heuristic"),
    app_commands.Choice(name="Random (Basic)", value="random")
])
async def start_wizard(
    interaction: discord.Interaction, 
    rounds: Optional[int] = None, 
    total_players: int = 3,
    bid_restriction: bool = True, 
    blind_round_one: bool = True,
    bot_type: str = "heuristic"
):
    channel_id = interaction.channel_id
    if channel_id in games:
        await interaction.response.send_message("A game is already in progress in this channel!", ephemeral=True)
        return

    if not (3 <= total_players <= 6):
        await interaction.response.send_message("❌ Total players must be between 3 and 6.", ephemeral=True)
        return

    games[channel_id] = {
        "host": interaction.user, 
        "players": [interaction.user], 
        "max_players": total_players,
        "rounds": rounds, 
        "bid_restriction": bid_restriction,
        "blind_round_one": blind_round_one,
        "bot_type": bot_type,
        "started": False
    }

    round_msg = f"**{rounds} rounds**" if rounds else "**Full Game (Max Rounds)**"
    await interaction.response.send_message(
        f"🧙 **Wizard lobby opened by {interaction.user.mention}!**\n"
        f"⚙️ **Size:** {total_players} players max | **Length:** {round_msg} | Bid Restriction: `{bid_restriction}` | Blind Round 1: `{blind_round_one}` | Bot Type: `{bot_type}`\n"
        f"Type `/join_wizard` to join."
    )


@bot.tree.command(name="join_wizard", description="Join the active Wizard lobby")
async def join_wizard(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    if channel_id not in games or games[channel_id]["started"]:
        await interaction.response.send_message("No open Wizard lobby in this channel.", ephemeral=True)
        return
    
    lobby = games[channel_id]
    if interaction.user in lobby["players"]:
        await interaction.response.send_message("You are already in the lobby!", ephemeral=True)
        return
    
    if len(lobby["players"]) >= lobby["max_players"]:
        await interaction.response.send_message(f"❌ This lobby is already full ({lobby['max_players']} players maximum).", ephemeral=True)
        return

    lobby["players"].append(interaction.user)
    player_names = ", ".join([p.display_name for p in lobby["players"]])
    await interaction.response.send_message(f"✅ {interaction.user.mention} joined! Players ({len(lobby['players'])}/{lobby['max_players']}): {player_names}")


@bot.tree.command(name="begin_game", description="Host begins the game")
async def begin_game(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    if channel_id not in games:
        await interaction.response.send_message("No game lobby exists.", ephemeral=True)
        return

    lobby = games[channel_id]
    if interaction.user != lobby["host"]:
        await interaction.response.send_message("Only the host can start the match.", ephemeral=True)
        return

    players = list(lobby["players"])
    max_players = lobby.get("max_players", 3)
    bot_type = lobby.get("bot_type", "heuristic")
    bot_count = 1
    
    while len(players) < max_players:
        bot_name = f"WizardBot-{bot_count}"
        if bot_type == "heuristic":
            bot_agent = HeuristicAgent(bot_name)
        else:
            bot_agent = RandomAgent(bot_name)
            
        bot_player = BotPlayer(bot_name, bot_agent)
        players.append(bot_player)
        bot_count += 1

    lobby["started"] = True
    player_list_str = ", ".join([p.display_name for p in players])
    await interaction.response.send_message(f"🚀 **Wizard game starting now! Check your Direct Messages.**\nPlayers ({len(players)}): {player_list_str} (Bot Type: `{bot_type}`)")
    
    game = DiscordWizardGame(
        channel=interaction.channel, 
        players=players, 
        num_rounds=lobby["rounds"],
        enable_bid_restriction=lobby["bid_restriction"],
        blind_round_one=lobby["blind_round_one"]
    )
    lobby["game_instance"] = game
    
    await game.start()
    if channel_id in games:
        del games[channel_id]


@bot.tree.command(name="stop_wizard", description="Stop the active Wizard game and display current scores")
async def stop_wizard(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    if channel_id not in games or not games[channel_id].get("started"):
        await interaction.response.send_message("No active Wizard game is running in this channel.", ephemeral=True)
        return

    lobby = games[channel_id]
    game_instance = lobby.get("game_instance")
    
    if game_instance:
        final_embed = discord.Embed(title="🛑 GAME STOPPED - Current Standings", color=discord.Color.orange())
        for p_id in range(game_instance.num_players):
            final_embed.add_field(
                name=game_instance.players[p_id].display_name, 
                value=f"**{game_instance.state.scores.get(p_id, 0)}** pts", 
                inline=True
            )
        
        for p_id in range(game_instance.num_players):
            await game_instance.render_and_update(p_id, final_embed)
        
        await interaction.response.send_message(embed=final_embed)
    
    del games[channel_id]


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


if __name__ == "__main__":
    bot.run(TOKEN)