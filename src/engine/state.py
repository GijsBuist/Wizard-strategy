# src/engine/state.py
from typing import Optional, List, Dict, Tuple
from src.engine.card import Card, CardType, Suit
from src.engine.deck import Deck
from src.engine.rules import determine_trick_winner

class GameState:
    def __init__(self, num_players: int, round_number: int = 1):
        self.num_players = num_players
        self.round_number = round_number
        self.dealer_id = 0
        self.current_player = 0
        
        # Player mappings
        self.hands: Dict[int, List[Card]] = {i: [] for i in range(num_players)}
        self.bids: Dict[int, Optional[int]] = {i: None for i in range(num_players)}
        self.tricks_won: Dict[int, int] = {i: 0 for i in range(num_players)}
        self.scores: Dict[int, int] = {i: 0 for i in range(num_players)}
        
        # Round & Trick tracking
        self.trump_card: Optional[Card] = None
        self.trump_suit: Optional[Suit] = None
        self.lead_suit: Optional[Suit] = None
        self.current_trick: List[Tuple[int, Card]] = []
        self.last_trick: List[Tuple[int, Card]] = []

    def start_round(self, deck: Deck, dealer_chosen_suit: Optional[Suit] = None):
        """Resets round state and deals cards."""
        self.current_trick = []
        self.last_trick = []
        self.lead_suit = None
        self.bids = {i: None for i in range(self.num_players)}
        self.tricks_won = {i: 0 for i in range(self.num_players)}
        
        raw_hands, self.trump_card = deck.deal(self.num_players, self.round_number)
        self.hands = {i: raw_hands[i] for i in range(self.num_players)}
        
        # Determine Trump Suit
        if self.trump_card is None or self.trump_card.card_type == CardType.JESTER:
            self.trump_suit = None
        elif self.trump_card.card_type == CardType.WIZARD:
            # Dealer picks trump suit before bidding begins
            self.trump_suit = dealer_chosen_suit
        else:
            self.trump_suit = self.trump_card.suit

        self.current_player = (self.dealer_id + 1) % self.num_players

    def record_bid(self, player_id: int, bid: int):
        self.bids[player_id] = bid

    def play_card(self, player_id: int, card: Card) -> Optional[int]:
        """Plays a card to the current trick. Returns winner_id if trick concludes."""
        if card in self.hands[player_id]:
            self.hands[player_id].remove(card)
            
        # Determine lead suit if first card of the trick
        if not self.current_trick:
            if card.card_type == CardType.WIZARD or card.card_type == CardType.JESTER:
                self.lead_suit = None
            else:
                self.lead_suit = card.suit
                
        self.current_trick.append((player_id, card))
        
        # Check if trick finished
        if len(self.current_trick) == self.num_players:
            winner_id = determine_trick_winner(self.current_trick, self.trump_suit, self.lead_suit)
            self.tricks_won[winner_id] += 1
            self.last_trick = list(self.current_trick)
            self.current_trick = []
            self.lead_suit = None
            self.current_player = winner_id
            return winner_id

        self.current_player = (player_id + 1) % self.num_players
        return None

    def calculate_round_scores(self) -> Dict[int, int]:
        """Calculates and updates round scores according to standard Wizard rules."""
        round_scores = {}
        for p_id in range(self.num_players):
            bid = self.bids[p_id]
            won = self.tricks_won[p_id]
            
            if bid == won:
                pts = 20 + (won * 10)
            else:
                pts = -10 * abs(bid - won)
                
            round_scores[p_id] = pts
            self.scores[p_id] += pts
            
        return round_scores