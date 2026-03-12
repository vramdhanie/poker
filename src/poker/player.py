"""Player classes: Human and AI."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cards import Card


class Action(Enum):
    FOLD   = auto()
    CHECK  = auto()
    CALL   = auto()
    RAISE  = auto()
    ALL_IN = auto()


@dataclass
class Player:
    name: str
    stack: int
    is_human: bool = False
    hole_cards: list[Card] = field(default_factory=list)
    current_bet: int = 0   # amount bet this round
    total_bet: int = 0     # total bet this hand
    folded: bool = False
    all_in: bool = False
    is_dealer: bool = False
    wins: int = 0
    hands_played: int = 0

    def reset_for_hand(self) -> None:
        self.hole_cards = []
        self.current_bet = 0
        self.total_bet = 0
        self.folded = False
        self.all_in = False

    def reset_for_round(self) -> None:
        self.current_bet = 0

    def can_act(self) -> bool:
        return not self.folded and not self.all_in and self.stack > 0

    def place_bet(self, amount: int) -> int:
        """Place a bet, capped at stack. Returns actual amount placed."""
        amount = min(amount, self.stack)
        self.stack -= amount
        self.current_bet += amount
        self.total_bet += amount
        if self.stack == 0:
            self.all_in = True
        return amount

    def __str__(self) -> str:
        return self.name


# ─── AI Strategy ─────────────────────────────────────────────────────────────

# AI personality profiles (affects aggression and bluff frequency)
AI_PROFILES = [
    {"name": "Alice", "aggression": 0.65, "bluff_rate": 0.12, "tightness": 0.55},
    {"name": "Bob",   "aggression": 0.80, "bluff_rate": 0.20, "tightness": 0.40},
    {"name": "Carol", "aggression": 0.50, "bluff_rate": 0.08, "tightness": 0.70},
]


class AIPlayer(Player):
    """
    AI player using a GTO-inspired strategy with:
    - Hand strength estimation via Monte Carlo
    - Pot odds calculation
    - Position awareness
    - Personality-based probabilistic variation
    """

    def __init__(self, profile: dict, stack: int) -> None:
        super().__init__(
            name=profile["name"],
            stack=stack,
            is_human=False,
        )
        self.aggression: float = profile["aggression"]
        self.bluff_rate: float = profile["bluff_rate"]
        self.tightness: float = profile["tightness"]
        self._street_aggression: float = 0.0  # tracks aggression this street

    def decide(
        self,
        community_cards: list[Card],
        pot: int,
        call_amount: int,
        min_raise: int,
        max_raise: int,
        position: int,        # 0=early, 1=middle, 2=late
        street: str,          # preflop/flop/turn/river
        num_active: int,
    ) -> tuple[Action, int]:
        """
        Return (Action, amount).
        amount is raise total (above current_bet) for RAISE, else 0.
        """
        from .evaluator import hand_strength, pot_odds as calc_pot_odds

        # --- Compute equity ---
        if self.hole_cards:
            equity = hand_strength(self.hole_cards, community_cards)
        else:
            equity = 0.5

        # Probabilistic noise to prevent predictability
        noise = random.gauss(0, 0.05)
        effective_equity = max(0.0, min(1.0, equity + noise))

        # Pot odds
        odds = calc_pot_odds(call_amount, pot)

        # Position bonus
        pos_bonus = position * 0.03  # late position = more aggressive

        # Bluffing
        is_bluff = random.random() < self.bluff_rate
        if is_bluff:
            effective_equity += random.uniform(0.15, 0.30)

        # Preflop tightness: fold weak hands more in early position
        if street == "preflop" and position == 0:
            effective_equity -= self.tightness * 0.1

        total_equity = min(1.0, effective_equity + pos_bonus)

        # --- Decision thresholds ---
        # Strong hand
        if total_equity > 0.70:
            if call_amount == 0:
                # Check or raise
                if random.random() < self.aggression and max_raise >= min_raise:
                    raise_size = self._compute_raise(pot, min_raise, max_raise, total_equity)
                    return (Action.RAISE, raise_size)
                return (Action.CHECK, 0)
            else:
                # Raise or call
                if random.random() < self.aggression and max_raise >= min_raise and call_amount < self.stack:
                    raise_size = self._compute_raise(pot, min_raise, max_raise, total_equity)
                    return (Action.RAISE, raise_size)
                if call_amount >= self.stack:
                    return (Action.ALL_IN, self.stack)
                return (Action.CALL, call_amount)

        # Medium hand
        elif total_equity > odds + 0.05:
            if call_amount == 0:
                if random.random() < self.aggression * 0.5 and max_raise >= min_raise:
                    raise_size = self._compute_raise(pot, min_raise, max_raise, total_equity)
                    return (Action.RAISE, raise_size)
                return (Action.CHECK, 0)
            else:
                if call_amount >= self.stack:
                    # Going all-in: only if equity is decent
                    if total_equity > 0.50:
                        return (Action.ALL_IN, self.stack)
                    return (Action.FOLD, 0)
                return (Action.CALL, call_amount)

        # Weak hand: fold or check
        else:
            if call_amount == 0:
                return (Action.CHECK, 0)
            # Occasionally bluff-call
            if is_bluff and call_amount < self.stack * 0.15:
                return (Action.CALL, call_amount)
            return (Action.FOLD, 0)

    def _compute_raise(self, pot: int, min_raise: int, max_raise: int, equity: float) -> int:
        """
        Size the raise based on equity and aggression.
        Returns the total raise amount (above current bet).
        """
        # Bet sizing: 0.5x to 2x pot, scaled by equity
        base = pot * (0.5 + equity * self.aggression)
        # Add noise
        base *= random.uniform(0.75, 1.25)
        amount = int(base)
        amount = max(min_raise, min(max_raise, amount))
        return amount
