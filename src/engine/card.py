from enum import IntEnum
from dataclasses import dataclass
from typing import Optional

class Suit(IntEnum):
    RED = 0
    YELLOW = 1 
    GREEN = 2
    BLUE = 3

class CardType(IntEnum):
    JESTER = 0
    STANDARD = 1
    WIZARD = 2 
 
@dataclass(frozen=True)
class Card:
    card_type: CardType
    suit: Optional[Suit] = None   # None for Jesters/Wizards or set when trump turned
    value: int = 0                # 1–13 for Standard; 0 for Jester; 14 for Wizard

    def __repr__(self):
        if self.card_type == CardType.WIZARD:
            return "🧙 Wizard"
        if self.card_type == CardType.JESTER:
            return "🃏 Jester"
        return f"{self.suit.name} {self.value}"

@dataclass
class PlayedCard:
    player_id: int
    card: Card

        