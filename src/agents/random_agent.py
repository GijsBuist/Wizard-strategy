# src/agents/random_agent.py
import random
from typing import Optional
from src.agents.base import BaseAgent
from src.engine.card import Card, Suit
from src.engine.rules import get_legal_plays
from src.engine.state import GameState

class RandomAgent:
    def __init__(self, name: str):
        self.name = name

    def select_bid(self, state: GameState, player_id: int, forbidden_bid: Optional[int] = None) -> int:
        max_bid = state.round_number
        legal_bids = [b for b in range(max_bid + 1) if b != forbidden_bid]
        
        if not legal_bids:
            legal_bids = list(range(max_bid + 1))
            
        import random
        return random.choice(legal_bids)
    
    def select_card(self, state: GameState, player_id: int) -> Card:
        from src.engine.rules import get_legal_plays
        hand = state.hands[player_id]
        playable = get_legal_plays(hand, state.lead_suit)
        import random
        return random.choice(playable)

    def select_trump(self, state: GameState, player_id: int) -> Suit:
        import random
        return random.choice(list(Suit))