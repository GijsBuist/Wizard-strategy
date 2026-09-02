# tests/test_deck.py
import pytest
from src.engine.card import CardType, Suit
from src.engine.deck import Deck, resolve_trump_suit

def test_deck_initialization():
    """Verify standard deck structure (60 total cards)."""
    deck = Deck()
    assert deck.size == 60

    # Count card types
    wizards = [c for c in deck.cards if c.card_type == CardType.WIZARD]
    jesters = [c for c in deck.cards if c.card_type == CardType.JESTER]
    standard = [c for c in deck.cards if c.card_type == CardType.STANDARD]

    assert len(wizards) == 4
    assert len(jesters) == 4
    assert len(standard) == 52

def test_deck_deal_round_one():
    """Test dealing round 1 for 4 players."""
    deck = Deck()
    hands, trump_card = deck.deal(num_players=4, round_number=1)

    # 4 players, 1 card each = 4 dealt cards + 1 trump card = 5 cards removed
    assert len(hands) == 4
    for p_id in range(4):
        assert len(hands[p_id]) == 1
    assert trump_card is not None
    assert deck.size == 55

def test_deck_deal_insufficient_cards():
    """Ensure dealing fails if deck doesn't have enough cards."""
    deck = Deck()
    with pytest.raises(ValueError):
        deck.deal(num_players=4, round_number=20)  # Needs 80 cards, deck only has 60

def test_resolve_trump_suit_standard():
    """Standard card revealed becomes trump."""
    deck = Deck()
    standard_card = [c for c in deck.cards if c.card_type == CardType.STANDARD and c.suit == Suit.RED][0]
    assert resolve_trump_suit(standard_card) == Suit.RED

def test_resolve_trump_suit_jester():
    """Jester revealed results in no trump suit."""
    deck = Deck()
    jester_card = [c for c in deck.cards if c.card_type == CardType.JESTER][0]
    assert resolve_trump_suit(jester_card) is None

def test_resolve_trump_suit_wizard():
    """Wizard revealed requires dealer choice."""
    deck = Deck()
    wizard_card = [c for c in deck.cards if c.card_type == CardType.WIZARD][0]

    # Dealer chooses GREEN
    assert resolve_trump_suit(wizard_card, dealer_chosen_suit=Suit.GREEN) == Suit.GREEN

    # Unset dealer choice should raise ValueError
    with pytest.raises(ValueError):
        resolve_trump_suit(wizard_card, dealer_chosen_suit=None)