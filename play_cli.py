# play_cli.py
from src.engine.card import Card, CardType, Suit
from src.engine.deck import Deck
from src.engine.rules import get_legal_plays
from src.engine.state import GameState

def render_hand(hand: list[Card]) -> None:
    """Displays player's hand with indexed choices."""
    for idx, card in enumerate(hand):
        print(f"  [{idx}] {card}")

def prompt_card_choice(hand: list[Card], lead_suit: Suit) -> Card:
    """Prompts player to pick a valid card from hand."""
    playable = get_legal_plays(hand, lead_suit)
    while True:
        try:
            choice = int(input("Select card index to play: "))
            if 0 <= choice < len(hand):
                card = hand[choice]
                if card in playable:
                    return card
                print(f"Illegal move! You must follow lead suit ({lead_suit.name}) if possible.")
            else:
                print("Index out of range.")
        except ValueError:
            print("Please enter a valid integer.")

def prompt_trump_choice() -> Suit:
    """Prompts dealer to pick a trump suit when a Wizard is revealed."""
    suits = list(Suit)
    print("\nA Wizard was turned up! Dealer gets to select the trump suit:")
    for idx, suit in enumerate(suits):
        print(f"  [{idx}] {suit.name}")
    while True:
        try:
            choice = int(input("Dealer, select trump suit index: "))
            if 0 <= choice < len(suits):
                return suits[choice]
            print("Index out of range.")
        except ValueError:
            print("Please enter a valid integer.")

def play_game(num_players: int = 3, num_rounds: int = 3):
    print("=" * 45)
    print("        WELCOME TO WIZARD (CLI PLAY)     ")
    print("=" * 45)

    deck = Deck()
    state = GameState(num_players=num_players, round_number=1)

    for round_num in range(1, num_rounds + 1):
        state.round_number = round_num
        
        # Calculate starting player for this round (left of dealer)
        starting_player = (state.dealer_id + 1) % num_players

        # Peek at trump card to see if dealer choice is required
        deck.reset()
        deck.shuffle()
        
        # Determine trump card before formal state setup
        temp_hands, temp_trump = deck.deal(num_players, round_num)
        dealer_choice = None
        if temp_trump and temp_trump.card_type == CardType.WIZARD:
            print(f"\nDealer is Player {state.dealer_id}.")
            dealer_choice = prompt_trump_choice()

        # Re-initialize round with chosen trump suit
        deck.reset()
        deck.shuffle()
        state.start_round(deck, dealer_chosen_suit=dealer_choice)
        
        print(f"\n=============================================")
        print(f"              START OF ROUND {round_num}")
        print(f"=============================================")
        print(f" Dealer: Player {state.dealer_id}")
        print(f" LEADER (Bidding & Play): Player {starting_player}")
        print(f" Trump Card Turned: {state.trump_card}")
        trump_str = state.trump_suit.name if state.trump_suit else "None (Jester/No Card)"
        print(f" Active Trump Suit: {trump_str}")
        print(f"=============================================\n")

        # --- BIDDING PHASE ---
        print("--- BIDDING PHASE ---")
        for _ in range(num_players):
            curr_bidding_p = state.current_player
            print(f"\nPlayer {curr_bidding_p}'s Hand:")
            render_hand(state.hands[curr_bidding_p])
            
            while True:
                try:
                    bid = int(input(f"Player {curr_bidding_p}, enter your bid (0-{round_num}): "))
                    if 0 <= bid <= round_num:
                        state.record_bid(curr_bidding_p, bid)
                        break
                    print(f"Bid must be between 0 and {round_num}.")
                except ValueError:
                    print("Enter a valid integer.")
            
            # Move to next bidder
            state.current_player = (state.current_player + 1) % num_players

        # Play/Bidding start position resets to left of dealer for the first trick
        state.current_player = starting_player

        # --- PLAYING PHASE ---
        for trick_num in range(round_num):
            print(f"\n=============================================")
            print(f" TRICK {trick_num + 1}/{round_num} | LEADER: Player {state.current_player}")
            print(f"=============================================")

            for _ in range(num_players):
                curr_p = state.current_player
                print(f"\n--- Player {curr_p}'s Turn ---")
                print(f"Current Trick on Table: {[f'P{p}: {c}' for p, c in state.current_trick]}")
                print(f"Lead Suit: {state.lead_suit.name if state.lead_suit else 'None'}")
                print(f"Your Hand:")
                render_hand(state.hands[curr_p])

                card = prompt_card_choice(state.hands[curr_p], state.lead_suit)
                winner = state.play_card(curr_p, card)

                if winner is not None:
                    print(f"\n****************************************")
                    print(f"   *** Player {winner} WON Trick {trick_num + 1}! ***")
                    print(f"****************************************")

        # --- SCORING PHASE ---
        round_pts = state.calculate_round_scores()
        print("\n=== ROUND SUMMARY ===")
        for p in range(num_players):
            print(f"Player {p} | Bid: {state.bids[p]} | Won: {state.tricks_won[p]} | Round Pts: {round_pts[p]} | Total Score: {state.scores[p]}")

        # Rotate dealer for next round
        state.dealer_id = (state.dealer_id + 1) % num_players

    print("\n=============================================")
    print("           GAME OVER - FINAL SCORES          ")
    print("=============================================")
    for p, score in state.scores.items():
        print(f"Player {p}: {score} points")

if __name__ == "__main__":
    play_game(num_players=3, num_rounds=3)