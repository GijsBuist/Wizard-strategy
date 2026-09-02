# src/agents/base.py
from abc import ABC, abstractmethod
from src.engine.card import Card, Suit
from src.engine.state import GameState

class BaseAgent(ABC):
    """Abstract base class for all Wizard agents."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def select_bid(self, state: GameState, player_id: int) -> int:
        """Returns the number of tricks this agent bids to win."""
        pass

    @abstractmethod
    def select_card(self, state: GameState, player_id: int) -> Card:
        """Returns the card chosen to play from legal plays in hand."""
        pass

    @abstractmethod
    def select_trump(self, state: GameState, player_id: int) -> Suit:
        """Selects trump suit if dealer turns over a Wizard card."""
        pass