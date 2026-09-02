# src/engine/deck.py
import random
from typing import Optional
from src.engine.card import Card, CardType, Suit

class Deck:
    """Manages the 60-card Wizard deck, shuffling, dealing, and trump selection."""

    def __init__(self) -> None:
        self.cards: list[Card] = []
        self.reset()

    def reset(self) -> None:
        """Rebuilds the standard 60-card Wizard deck and resets state."""
        self.cards = []

        # 1. Add 52 standard cards (Values 1 through 13 for each of the 4 suits)
        for suit in Suit:
            for val in range(1, 14):
                self.cards.append(Card(card_type=CardType.STANDARD, suit=suit, value=val))

        # 2. Add 4 Wizards
        for _ in range(4):
            self.cards.append(Card(card_type=CardType.WIZARD, suit=None, value=14))

        # 3. Add 4 Jesters
        for _ in range(4):
            self.cards.append(Card(card_type=CardType.JESTER, suit=None, value=0))

    def shuffle(self) -> None:
        """Shuffles the deck in place."""
        random.shuffle(self.cards)

    def deal(self, num_players: int, round_number: int) -> tuple[dict[int, list[Card]], Optional[Card]]:
        """
        Deals hands to players for the given round and turns over the trump card.

        Args:
            num_players: Total number of active players (typically 3 to 6).
            round_number: Current round number (1 up to 60 / num_players).

        Returns:
            A tuple containing:
            - hands: Dictionary mapping player_id (0..num_players-1) to list of Cards.
            - trump_card: The revealed Card turned up from the deck, or None if all cards were dealt.
        """
        if self.size < num_players * round_number:
            raise ValueError(f"Not enough cards in deck to deal {round_number} card(s) to {num_players} players.")

        hands: dict[int, list[Card]] = {p: [] for p in range(num_players)}

        # Deal cards round-robin
        for _ in range(round_number):
            for p in range(num_players):
                hands[p].append(self.cards.pop())

        # Turn over trump card if any cards remain in the deck
        trump_card: Optional[Card] = self.cards.pop() if self.cards else None

        return hands, trump_card

    @property
    def size(self) -> int:
        """Returns number of cards remaining in the deck."""
        return len(self.cards)


def resolve_trump_suit(trump_card: Optional[Card], dealer_chosen_suit: Optional[Suit] = None) -> Optional[Suit]:
    """
    Determines the active trump suit based on the turned-up trump card.

    Args:
        trump_card: The card turned face up from the deck after dealing (or None if last round).
        dealer_chosen_suit: Optional suit chosen by the dealer if trump_card is a Wizard.

    Returns:
        The active Suit, or None if there is no trump (Jester revealed or last round).
    """
    if trump_card is None:
        return None  # Last round (all cards dealt), no trump card turned

    if trump_card.card_type == CardType.STANDARD:
        return trump_card.suit

    if trump_card.card_type == CardType.JESTER:
        return None  # Turned Jester means no trump suit for the round

    if trump_card.card_type == CardType.WIZARD:
        if dealer_chosen_suit is None:
            raise ValueError("Dealer must pick a suit when a Wizard is turned over for trump.")
        return dealer_chosen_suit

    return None