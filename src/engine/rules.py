# src/engine/rules.py
from typing import List, Optional, Tuple
from src.engine.card import Card, CardType, Suit


def get_legal_plays(hand: List[Card], lead_suit: Optional[Suit]) -> List[Card]:
    """Returns a list of playable cards from the hand given the lead suit."""
    if lead_suit is None:
        return hand

    # Check if the player has any standard card matching the lead suit
    has_lead_suit = any(c.card_type == CardType.STANDARD and c.suit == lead_suit for c in hand)

    # If player holds the lead suit, they must play either a lead suit card, a Wizard, or a Jester
    if has_lead_suit:
        return [
            c for c in hand 
            if (c.card_type == CardType.STANDARD and c.suit == lead_suit)
            or c.card_type in (CardType.WIZARD, CardType.JESTER)
        ]

    # If player has no lead suit cards, they can play ANY card in their hand
    return hand


def evaluate_trick(
    trick: List[Tuple[int, Card]], 
    trump_suit: Optional[Suit], 
    lead_suit: Optional[Suit]
) -> int:
    """
    Determines the winner of a trick according to standard Wizard rules:
    1. First Wizard played wins.
    2. If no Wizard, highest card of trump suit wins.
    3. If no trump card, highest card of lead suit wins.
    4. If all cards are Jesters, the first Jester wins.
    """
    if not trick:
        raise ValueError("Cannot determine winner of an empty trick.")

    # 1. First Wizard played wins
    for player_id, card in trick:
        if card.card_type == CardType.WIZARD:
            return player_id

    # 2. Highest card of Trump suit
    if trump_suit is not None:
        trump_cards = [
            (player_id, card) for player_id, card in trick 
            if card.card_type == CardType.STANDARD and card.suit == trump_suit
        ]
        if trump_cards:
            return max(trump_cards, key=lambda item: item[1].value)[0]

    # 3. Highest card of Lead suit
    if lead_suit is not None:
        lead_cards = [
            (player_id, card) for player_id, card in trick 
            if card.card_type == CardType.STANDARD and card.suit == lead_suit
        ]
        if lead_cards:
            return max(lead_cards, key=lambda item: item[1].value)[0]

    # 4. Fallback: First played non-Jester card wins; if all are Jesters, first Jester wins
    non_jesters = [
        (player_id, card) for player_id, card in trick 
        if card.card_type != CardType.JESTER
    ]
    if non_jesters:
        return non_jesters[0][0]

    return trick[0][0]


determine_trick_winner = evaluate_trick