# src/agents/heuristic_agent.py
import random
from typing import Optional
from src.agents.base import BaseAgent
from src.engine.card import Card, CardType, Suit
from src.engine.rules import get_legal_plays
from src.engine.state import GameState

class HeuristicAgent(BaseAgent):
    """A smarter rule-based agent that evaluates hands, respects bid restrictions, and tries to meet its target tricks."""

    def __init__(self, name: str = "WizardPro"):
        super().__init__(name)

    def select_bid(self, state: GameState, player_id: int, forbidden_bid: Optional[int] = None) -> int:
        hand = state.hands[player_id]
        max_bid = state.round_number

        # Heuristic estimation of trick-winning potential
        estimated_wins = 0.0
        for card in hand:
            if card.card_type == CardType.WIZARD:
                estimated_wins += 1.0
            elif card.card_type == CardType.STANDARD and card.value >= 12:
                estimated_wins += 0.6
            elif card.card_type == CardType.STANDARD and card.value == 11:
                estimated_wins += 0.3

        bid = max(0, min(round(estimated_wins), max_bid))

        # Respect the forbidden bid restriction if applied
        if bid == forbidden_bid:
            if bid > 0:
                bid -= 1
            else:
                bid += 1

        return min(max(bid, 0), max_bid)

    def select_card(self, state: GameState, player_id: int) -> Card:
        hand = state.hands[player_id]
        legal = get_legal_plays(hand, state.lead_suit)

        current_bids = state.bids if isinstance(state.bids, dict) else {}
        my_bid = current_bids.get(player_id, 0)
        my_wins = state.tricks_won.get(player_id, 0)
        
        need_tricks = my_wins < my_bid

        def card_power(c: Card):
            if c.card_type == CardType.WIZARD:
                return 100
            if c.card_type == CardType.JESTER:
                return -1
            return c.value

        sorted_legal = sorted(legal, key=card_power, reverse=True)

        if need_tricks:
            # Play highest card to capture the trick
            return sorted_legal[0]
        else:
            # Play lowest card (Jester or low numbers) to duck the trick
            return sorted_legal[-1]

    def select_trump(self, state: GameState, player_id: int) -> Suit:
        hand = state.hands[player_id]
        suit_counts = {suit: 0 for suit in Suit}
        for card in hand:
            if card.card_type == CardType.STANDARD:
                suit_counts[card.suit] += 1
        
        # Pick the suit the agent holds the most cards in
        return max(suit_counts, key=suit_counts.get)