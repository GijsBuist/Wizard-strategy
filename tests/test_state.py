# tests/test_state.py
import random
import pytest
from src.engine.card import Card, CardType, Suit
from src.engine.deck import Deck
from src.engine.state import GameState

def test_turn_order_and_trick_winner_lead():
    """Verify player turn advances and trick winner leads next trick."""
    state = GameState(num_players=3, round_number=1)
    deck = Deck()
    state.start_round(deck)
    
    start_player = state.current_player
    
    # Simulate playing 3 cards manually
    card_p0 = state.hands[start_player][0]
    state.play_card(start_player, card_p0)
    
    p2 = state.current_player
    card_p1 = state.hands[p2][0]
    state.play_card(p2, card_p1)
    
    p3 = state.current_player
    card_p2 = state.hands[p3][0]
    winner = state.play_card(p3, card_p2)
    
    # Winner should be set as active player for next trick
    assert winner is not None
    assert state.current_player == winner

def test_round_scoring_exact_and_missed():
    """Verify +20 (+10/trick) for exact bids and -10/trick for missed bids."""
    state = GameState(num_players=3, round_number=3)
    state.bids = {0: 2, 1: 0, 2: 1}
    state.tricks_won = {0: 2, 1: 1, 2: 0}  # P0 exact (+40), P1 over (+1 trick off), P2 under (-1 trick off)
    
    scores = state.calculate_round_scores()
    
    assert scores[0] == 40   # 20 + (2 * 10)
    assert scores[1] == -10  # 1 trick off
    assert scores[2] == -10  # 1 trick off
    assert state.scores[0] == 40

def test_fuzz_random_auto_play_rounds():
    """Fuzz test: execute 1,000 completely random rounds to verify state stability without exceptions."""
   
    for _ in range(1000):
        deck = Deck()
        deck.shuffle()

        state = GameState(num_players=4, round_number=3)
        
        # Pass a default dealer choice (e.g. Suit.RED) in case a Wizard is turned up as trump
        state.start_round(deck, dealer_chosen_suit=Suit.RED)
        
        # Record random valid bids
        for p in range(4):
            state.record_bid(p, random.randint(0, 3))
            
        # Play out all tricks in round
        for _ in range(3):  # 3 tricks per player in round 3
            for _ in range(4):
                curr = state.current_player
                legal = state.hands[curr]
                
                # Filter legal moves based on rules engine
                from src.engine.rules import get_legal_plays
                playable = get_legal_plays(legal, state.lead_suit)
                
                chosen_card = random.choice(playable)
                state.play_card(curr, chosen_card)
                
        # Calculate final scores
        round_pts = state.calculate_round_scores()
        assert len(round_pts) == 4