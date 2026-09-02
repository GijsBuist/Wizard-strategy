# tests/test_rules.py
import pytest
from src.engine.card import Card, CardType, Suit
from src.engine.rules import get_legal_plays, evaluate_trick


def test_get_legal_plays_must_follow_suit():
    red_5 = Card(CardType.STANDARD, Suit.RED, 5)
    blue_7 = Card(CardType.STANDARD, Suit.BLUE, 7)
    hand = [red_5, blue_7]

    legal = get_legal_plays(hand, Suit.RED)
    assert legal == [red_5]


def test_get_legal_plays_wizard_always_allowed():
    wizard = Card(CardType.WIZARD)
    blue_7 = Card(CardType.STANDARD, Suit.BLUE, 7)
    hand = [wizard, blue_7]

    legal = get_legal_plays(hand, Suit.RED)
    assert wizard in legal


def test_evaluate_trick_highest_lead_suit_wins():
    c1 = (0, Card(CardType.STANDARD, Suit.RED, 5))
    c2 = (1, Card(CardType.STANDARD, Suit.RED, 10))
    trick = [c1, c2]

    winner = evaluate_trick(trick, trump_suit=None, lead_suit=Suit.RED)
    assert winner == 1


def test_evaluate_trick_wizard_beats_trump():
    c1 = (0, Card(CardType.STANDARD, Suit.BLUE, 13))  # Trump card
    c2 = (1, Card(CardType.WIZARD))
    trick = [c1, c2]

    winner = evaluate_trick(trick, trump_suit=Suit.BLUE, lead_suit=Suit.RED)
    assert winner == 1