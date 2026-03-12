"""Card and Deck representations with unicode suit icons."""

import random
from dataclasses import dataclass
from enum import IntEnum


class Suit(IntEnum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3


class Rank(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


SUIT_ICONS = {
    Suit.CLUBS:    "♣",
    Suit.DIAMONDS: "♦",
    Suit.HEARTS:   "♥",
    Suit.SPADES:   "♠",
}

SUIT_COLORS = {
    Suit.CLUBS:    "\033[37m",   # White/grey
    Suit.DIAMONDS: "\033[91m",   # Bright red
    Suit.HEARTS:   "\033[91m",   # Bright red
    Suit.SPADES:   "\033[37m",   # White/grey
}

RANK_NAMES = {
    Rank.TWO:   "2",
    Rank.THREE: "3",
    Rank.FOUR:  "4",
    Rank.FIVE:  "5",
    Rank.SIX:   "6",
    Rank.SEVEN: "7",
    Rank.EIGHT: "8",
    Rank.NINE:  "9",
    Rank.TEN:   "T",
    Rank.JACK:  "J",
    Rank.QUEEN: "Q",
    Rank.KING:  "K",
    Rank.ACE:   "A",
}

RESET = "\033[0m"


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        color = SUIT_COLORS[self.suit]
        icon = SUIT_ICONS[self.suit]
        rank = RANK_NAMES[self.rank]
        return f"{color}{rank}{icon}{RESET}"

    def __repr__(self) -> str:
        return f"Card({RANK_NAMES[self.rank]}{SUIT_ICONS[self.suit]})"

    def plain(self) -> str:
        """Plain text without color codes."""
        return f"{RANK_NAMES[self.rank]}{SUIT_ICONS[self.suit]}"


HIDDEN_CARD = "\033[90m[??]\033[0m"


def format_hand(cards: list[Card], hide: bool = False) -> str:
    """Format a list of cards for display."""
    if not cards:
        return "[ ]"
    if hide:
        return "  ".join(HIDDEN_CARD for _ in cards)
    return "  ".join(f"[{c}]" for c in cards)


def format_community(cards: list[Card], total: int = 5) -> str:
    """Format community cards, showing placeholders for unrevealed cards."""
    shown = [f"[{c}]" for c in cards]
    hidden = ["\033[90m[  ]\033[0m"] * (total - len(cards))
    return "  ".join(shown + hidden)


class Deck:
    def __init__(self) -> None:
        self._cards: list[Card] = [
            Card(rank, suit)
            for suit in Suit
            for rank in Rank
        ]

    def shuffle(self) -> None:
        random.shuffle(self._cards)

    def deal(self, n: int = 1) -> list[Card]:
        if n > len(self._cards):
            raise ValueError("Not enough cards in deck")
        dealt = self._cards[-n:]
        self._cards = self._cards[:-n]
        return dealt

    def deal_one(self) -> Card:
        return self.deal(1)[0]

    def __len__(self) -> int:
        return len(self._cards)
