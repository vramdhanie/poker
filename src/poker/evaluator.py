"""
Poker hand evaluator using a fast rank-based approach.
Returns a tuple (hand_rank, tiebreakers) where higher is better.
"""

from collections import Counter
from itertools import combinations

from .cards import Card, Rank, Suit


# Hand rankings (higher = better)
class HandRank:
    HIGH_CARD       = 0
    ONE_PAIR        = 1
    TWO_PAIR        = 2
    THREE_OF_A_KIND = 3
    STRAIGHT        = 4
    FLUSH           = 5
    FULL_HOUSE      = 6
    FOUR_OF_A_KIND  = 7
    STRAIGHT_FLUSH  = 8
    ROYAL_FLUSH     = 9


HAND_NAMES = {
    HandRank.HIGH_CARD:       "High Card",
    HandRank.ONE_PAIR:        "One Pair",
    HandRank.TWO_PAIR:        "Two Pair",
    HandRank.THREE_OF_A_KIND: "Three of a Kind",
    HandRank.STRAIGHT:        "Straight",
    HandRank.FLUSH:           "Flush",
    HandRank.FULL_HOUSE:      "Full House",
    HandRank.FOUR_OF_A_KIND:  "Four of a Kind",
    HandRank.STRAIGHT_FLUSH:  "Straight Flush",
    HandRank.ROYAL_FLUSH:     "Royal Flush",
}


def _evaluate_five(cards: list[Card]) -> tuple[int, list[int]]:
    """Evaluate exactly 5 cards. Returns (hand_rank, tiebreaker_list)."""
    ranks = sorted([c.rank for c in cards], reverse=True)
    suits = [c.suit for c in cards]
    rank_counts = Counter(ranks)

    is_flush = len(set(suits)) == 1

    # Check straight (including A-2-3-4-5 wheel)
    unique_ranks = sorted(set(int(r) for r in ranks), reverse=True)
    is_straight = False
    straight_high = 0
    if len(unique_ranks) == 5:
        if unique_ranks[0] - unique_ranks[4] == 4:
            is_straight = True
            straight_high = unique_ranks[0]
        # Wheel: A-2-3-4-5
        elif unique_ranks == [14, 5, 4, 3, 2]:
            is_straight = True
            straight_high = 5

    counts = sorted(rank_counts.values(), reverse=True)
    rank_vals = sorted(rank_counts.keys(), key=lambda r: (rank_counts[r], int(r)), reverse=True)

    if is_straight and is_flush:
        if straight_high == 14:
            return (HandRank.ROYAL_FLUSH, [straight_high])
        return (HandRank.STRAIGHT_FLUSH, [straight_high])

    if counts[0] == 4:
        quad_rank = [r for r, c in rank_counts.items() if c == 4][0]
        kicker = [r for r, c in rank_counts.items() if c == 1][0]
        return (HandRank.FOUR_OF_A_KIND, [int(quad_rank), int(kicker)])

    if counts[0] == 3 and counts[1] == 2:
        three_rank = [r for r, c in rank_counts.items() if c == 3][0]
        pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
        return (HandRank.FULL_HOUSE, [int(three_rank), int(pair_rank)])

    if is_flush:
        return (HandRank.FLUSH, [int(r) for r in ranks])

    if is_straight:
        return (HandRank.STRAIGHT, [straight_high])

    if counts[0] == 3:
        three_rank = [r for r, c in rank_counts.items() if c == 3][0]
        kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
        return (HandRank.THREE_OF_A_KIND, [int(three_rank)] + [int(k) for k in kickers])

    if counts[0] == 2 and counts[1] == 2:
        pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
        kicker = [r for r, c in rank_counts.items() if c == 1][0]
        return (HandRank.TWO_PAIR, [int(pairs[0]), int(pairs[1]), int(kicker)])

    if counts[0] == 2:
        pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
        kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
        return (HandRank.ONE_PAIR, [int(pair_rank)] + [int(k) for k in kickers])

    return (HandRank.HIGH_CARD, [int(r) for r in ranks])


def best_hand(hole_cards: list[Card], community_cards: list[Card]) -> tuple[int, list[int], list[Card]]:
    """
    Find the best 5-card hand from hole + community cards (7 total usually).
    Returns (hand_rank, tiebreakers, best_5_cards).
    """
    all_cards = hole_cards + community_cards
    best = None
    best_five: list[Card] = []

    for combo in combinations(all_cards, 5):
        result = _evaluate_five(list(combo))
        if best is None or result > best:
            best = result
            best_five = list(combo)

    assert best is not None
    return (best[0], best[1], best_five)


def hand_name(hand_rank: int) -> str:
    return HAND_NAMES.get(hand_rank, "Unknown")


def hand_strength(hole_cards: list[Card], community_cards: list[Card]) -> float:
    """
    Estimate hand strength as a value 0..1 using Monte Carlo simulation.
    Used by the AI for decision making.
    """
    import random
    from .cards import Deck, Suit, Rank as R

    # Build remaining deck
    known = set(hole_cards + community_cards)
    remaining = [
        Card(rank, suit)
        for suit in Suit
        for rank in R
        if Card(rank, suit) not in known
    ]

    num_opponents = 3
    num_simulations = 300
    wins = 0
    ties = 0

    for _ in range(num_simulations):
        deck_sample = remaining[:]
        random.shuffle(deck_sample)

        # Complete community cards to 5
        needed_community = 5 - len(community_cards)
        sim_community = community_cards + deck_sample[:needed_community]
        deck_sample = deck_sample[needed_community:]

        # Deal to opponents
        my_rank = best_hand(hole_cards, sim_community)[:2]
        won = True
        tied = False

        for _ in range(num_opponents):
            if len(deck_sample) < 2:
                break
            opp_hole = deck_sample[:2]
            deck_sample = deck_sample[2:]
            opp_rank = best_hand(opp_hole, sim_community)[:2]
            if opp_rank > my_rank:
                won = False
                tied = False
                break
            elif opp_rank == my_rank:
                tied = True

        if won and not tied:
            wins += 1
        elif tied:
            ties += 0.5

    return (wins + ties) / num_simulations


def pot_odds(call_amount: int, pot_size: int) -> float:
    """Return pot odds as a fraction (break-even equity needed)."""
    if call_amount <= 0:
        return 0.0
    total = pot_size + call_amount
    return call_amount / total
