"""Tests for evaluator.py — hand ranking, best_hand, hand_strength, pot_odds."""

import pytest
from poker.cards import Card, Rank, Suit
from poker.evaluator import (
    HandRank, HAND_NAMES,
    _evaluate_five, best_hand, hand_name, hand_strength, pot_odds,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def c(rank: Rank, suit: Suit) -> Card:
    return Card(rank, suit)


S, H, D, C = Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS


# ─── _evaluate_five ───────────────────────────────────────────────────────────

class TestEvaluateFive:
    """Exhaustive tests for the core 5-card evaluator."""

    # ── Royal Flush ──────────────────────────────────────────────────────────

    def test_royal_flush_spades(self):
        hand = [c(Rank.ACE, S), c(Rank.KING, S), c(Rank.QUEEN, S),
                c(Rank.JACK, S), c(Rank.TEN, S)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.ROYAL_FLUSH

    def test_royal_flush_hearts(self):
        hand = [c(Rank.ACE, H), c(Rank.KING, H), c(Rank.QUEEN, H),
                c(Rank.JACK, H), c(Rank.TEN, H)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.ROYAL_FLUSH

    # ── Straight Flush ────────────────────────────────────────────────────────

    def test_straight_flush_nine_high(self):
        hand = [c(Rank.NINE, S), c(Rank.EIGHT, S), c(Rank.SEVEN, S),
                c(Rank.SIX, S), c(Rank.FIVE, S)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.STRAIGHT_FLUSH
        assert tb == [9]

    def test_straight_flush_king_high(self):
        hand = [c(Rank.KING, H), c(Rank.QUEEN, H), c(Rank.JACK, H),
                c(Rank.TEN, H), c(Rank.NINE, H)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.STRAIGHT_FLUSH
        assert tb == [13]

    def test_straight_flush_wheel(self):
        """A-2-3-4-5 of same suit = straight flush (not royal)."""
        hand = [c(Rank.ACE, D), c(Rank.TWO, D), c(Rank.THREE, D),
                c(Rank.FOUR, D), c(Rank.FIVE, D)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.STRAIGHT_FLUSH
        assert tb == [5]

    # ── Four of a Kind ────────────────────────────────────────────────────────

    def test_four_aces(self):
        hand = [c(Rank.ACE, S), c(Rank.ACE, H), c(Rank.ACE, D),
                c(Rank.ACE, C), c(Rank.KING, S)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.FOUR_OF_A_KIND
        assert tb[0] == 14  # quad rank
        assert tb[1] == 13  # kicker

    def test_four_twos(self):
        hand = [c(Rank.TWO, S), c(Rank.TWO, H), c(Rank.TWO, D),
                c(Rank.TWO, C), c(Rank.ACE, S)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.FOUR_OF_A_KIND
        assert tb[0] == 2
        assert tb[1] == 14

    def test_four_of_a_kind_tiebreak_quad_rank(self):
        hand_kings = [c(Rank.KING, S), c(Rank.KING, H), c(Rank.KING, D),
                      c(Rank.KING, C), c(Rank.TWO, S)]
        hand_queens = [c(Rank.QUEEN, S), c(Rank.QUEEN, H), c(Rank.QUEEN, D),
                       c(Rank.QUEEN, C), c(Rank.ACE, S)]
        r_k, tb_k = _evaluate_five(hand_kings)
        r_q, tb_q = _evaluate_five(hand_queens)
        assert r_k == r_q == HandRank.FOUR_OF_A_KIND
        assert tb_k > tb_q  # kings quads beat queens quads

    # ── Full House ────────────────────────────────────────────────────────────

    def test_full_house_aces_over_kings(self):
        hand = [c(Rank.ACE, S), c(Rank.ACE, H), c(Rank.ACE, D),
                c(Rank.KING, S), c(Rank.KING, H)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.FULL_HOUSE
        assert tb[0] == 14
        assert tb[1] == 13

    def test_full_house_twos_over_threes(self):
        hand = [c(Rank.TWO, S), c(Rank.TWO, H), c(Rank.TWO, D),
                c(Rank.THREE, S), c(Rank.THREE, H)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.FULL_HOUSE
        assert tb[0] == 2
        assert tb[1] == 3

    def test_full_house_tiebreak_trips_rank(self):
        hand_aaa_kk = [c(Rank.ACE, S), c(Rank.ACE, H), c(Rank.ACE, D),
                       c(Rank.KING, S), c(Rank.KING, H)]
        hand_kkk_aa = [c(Rank.KING, S), c(Rank.KING, H), c(Rank.KING, D),
                       c(Rank.ACE, S), c(Rank.ACE, H)]
        r1, tb1 = _evaluate_five(hand_aaa_kk)
        r2, tb2 = _evaluate_five(hand_kkk_aa)
        assert r1 == r2 == HandRank.FULL_HOUSE
        assert (r1, tb1) > (r2, tb2)  # AAA beats KKK full house

    # ── Flush ─────────────────────────────────────────────────────────────────

    def test_flush_ace_high(self):
        hand = [c(Rank.ACE, S), c(Rank.KING, S), c(Rank.NINE, S),
                c(Rank.FIVE, S), c(Rank.TWO, S)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.FLUSH
        assert tb[0] == 14

    def test_flush_not_straight(self):
        """Non-sequential same-suit hand is flush, not straight flush."""
        hand = [c(Rank.ACE, H), c(Rank.JACK, H), c(Rank.NINE, H),
                c(Rank.SIX, H), c(Rank.TWO, H)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.FLUSH

    def test_flush_tiebreak_by_highest_card(self):
        hand_ak = [c(Rank.ACE, S), c(Rank.KING, S), c(Rank.NINE, S),
                   c(Rank.FIVE, S), c(Rank.TWO, S)]
        hand_aq = [c(Rank.ACE, H), c(Rank.QUEEN, H), c(Rank.NINE, H),
                   c(Rank.FIVE, H), c(Rank.TWO, H)]
        r1, tb1 = _evaluate_five(hand_ak)
        r2, tb2 = _evaluate_five(hand_aq)
        assert r1 == r2 == HandRank.FLUSH
        assert (r1, tb1) > (r2, tb2)  # AK flush beats AQ flush

    # ── Straight ──────────────────────────────────────────────────────────────

    def test_straight_broadway(self):
        """A-K-Q-J-T straight."""
        hand = [c(Rank.ACE, S), c(Rank.KING, H), c(Rank.QUEEN, D),
                c(Rank.JACK, C), c(Rank.TEN, S)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.STRAIGHT
        assert tb == [14]

    def test_straight_wheel(self):
        """A-2-3-4-5 (wheel) — ace plays as low."""
        hand = [c(Rank.ACE, S), c(Rank.TWO, H), c(Rank.THREE, D),
                c(Rank.FOUR, C), c(Rank.FIVE, S)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.STRAIGHT
        assert tb == [5]  # high card is 5, not ace

    def test_straight_nine_high(self):
        hand = [c(Rank.NINE, S), c(Rank.EIGHT, H), c(Rank.SEVEN, D),
                c(Rank.SIX, C), c(Rank.FIVE, S)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.STRAIGHT
        assert tb == [9]

    def test_almost_straight_not_straight(self):
        """6-7-8-9-J is not a straight."""
        hand = [c(Rank.JACK, S), c(Rank.NINE, H), c(Rank.EIGHT, D),
                c(Rank.SEVEN, C), c(Rank.SIX, S)]
        rank, _ = _evaluate_five(hand)
        assert rank == HandRank.HIGH_CARD

    def test_straight_beats_flush_is_false(self):
        """Straight (4) ranks lower than flush (5)."""
        assert HandRank.STRAIGHT < HandRank.FLUSH

    # ── Three of a Kind ───────────────────────────────────────────────────────

    def test_three_aces(self):
        hand = [c(Rank.ACE, S), c(Rank.ACE, H), c(Rank.ACE, D),
                c(Rank.KING, C), c(Rank.QUEEN, S)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.THREE_OF_A_KIND
        assert tb[0] == 14
        assert tb[1] == 13  # best kicker
        assert tb[2] == 12  # second kicker

    def test_three_twos(self):
        hand = [c(Rank.TWO, S), c(Rank.TWO, H), c(Rank.TWO, D),
                c(Rank.ACE, C), c(Rank.KING, S)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.THREE_OF_A_KIND
        assert tb[0] == 2

    def test_three_of_a_kind_tiebreak_kickers(self):
        hand_ak = [c(Rank.THREE, S), c(Rank.THREE, H), c(Rank.THREE, D),
                   c(Rank.ACE, C), c(Rank.KING, S)]
        hand_aq = [c(Rank.THREE, C), c(Rank.THREE, S), c(Rank.THREE, H),
                   c(Rank.ACE, D), c(Rank.QUEEN, S)]
        r1, tb1 = _evaluate_five(hand_ak)
        r2, tb2 = _evaluate_five(hand_aq)
        assert r1 == r2 == HandRank.THREE_OF_A_KIND
        assert (r1, tb1) > (r2, tb2)  # same trips, A-K kickers beat A-Q

    # ── Two Pair ─────────────────────────────────────────────────────────────

    def test_two_pair_aces_and_kings(self):
        hand = [c(Rank.ACE, S), c(Rank.ACE, H), c(Rank.KING, D),
                c(Rank.KING, C), c(Rank.QUEEN, S)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.TWO_PAIR
        assert tb[0] == 14  # top pair
        assert tb[1] == 13  # bottom pair
        assert tb[2] == 12  # kicker

    def test_two_pair_twos_and_threes(self):
        hand = [c(Rank.TWO, S), c(Rank.TWO, H), c(Rank.THREE, D),
                c(Rank.THREE, C), c(Rank.ACE, S)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.TWO_PAIR
        assert tb[0] == 3
        assert tb[1] == 2

    def test_two_pair_tiebreak_top_pair(self):
        hand_aa_kk = [c(Rank.ACE, S), c(Rank.ACE, H), c(Rank.KING, D),
                      c(Rank.KING, C), c(Rank.TWO, S)]
        hand_aa_qq = [c(Rank.ACE, C), c(Rank.ACE, D), c(Rank.QUEEN, S),
                      c(Rank.QUEEN, H), c(Rank.TWO, H)]
        r1, tb1 = _evaluate_five(hand_aa_kk)
        r2, tb2 = _evaluate_five(hand_aa_qq)
        assert r1 == r2 == HandRank.TWO_PAIR
        assert (r1, tb1) > (r2, tb2)

    def test_two_pair_tiebreak_kicker(self):
        hand_k = [c(Rank.ACE, S), c(Rank.ACE, H), c(Rank.KING, D),
                  c(Rank.KING, C), c(Rank.QUEEN, S)]
        hand_j = [c(Rank.ACE, C), c(Rank.ACE, D), c(Rank.KING, S),
                  c(Rank.KING, H), c(Rank.JACK, S)]
        r1, tb1 = _evaluate_five(hand_k)
        r2, tb2 = _evaluate_five(hand_j)
        assert (r1, tb1) > (r2, tb2)  # queen kicker beats jack kicker

    # ── One Pair ─────────────────────────────────────────────────────────────

    def test_one_pair_aces(self):
        hand = [c(Rank.ACE, S), c(Rank.ACE, H), c(Rank.KING, D),
                c(Rank.QUEEN, C), c(Rank.JACK, S)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.ONE_PAIR
        assert tb[0] == 14
        assert tb[1] == 13
        assert tb[2] == 12
        assert tb[3] == 11

    def test_one_pair_twos(self):
        hand = [c(Rank.TWO, S), c(Rank.TWO, H), c(Rank.ACE, D),
                c(Rank.KING, C), c(Rank.QUEEN, S)]
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.ONE_PAIR
        assert tb[0] == 2

    def test_one_pair_tiebreak_pair_rank(self):
        hand_aa = [c(Rank.ACE, S), c(Rank.ACE, H), c(Rank.TWO, D),
                   c(Rank.THREE, C), c(Rank.FOUR, S)]
        hand_kk = [c(Rank.KING, S), c(Rank.KING, H), c(Rank.ACE, D),
                   c(Rank.QUEEN, C), c(Rank.JACK, S)]
        r1, tb1 = _evaluate_five(hand_aa)
        r2, tb2 = _evaluate_five(hand_kk)
        assert r1 == r2 == HandRank.ONE_PAIR
        assert (r1, tb1) > (r2, tb2)

    def test_one_pair_tiebreak_kickers(self):
        hand_k = [c(Rank.ACE, S), c(Rank.ACE, H), c(Rank.KING, D),
                  c(Rank.QUEEN, C), c(Rank.JACK, S)]
        hand_q = [c(Rank.ACE, C), c(Rank.ACE, D), c(Rank.QUEEN, S),
                  c(Rank.JACK, H), c(Rank.TEN, S)]
        r1, tb1 = _evaluate_five(hand_k)
        r2, tb2 = _evaluate_five(hand_q)
        assert (r1, tb1) > (r2, tb2)

    # ── High Card ─────────────────────────────────────────────────────────────

    def test_high_card_ace_high(self):
        hand = [c(Rank.ACE, S), c(Rank.KING, H), c(Rank.QUEEN, D),
                c(Rank.JACK, C), c(Rank.NINE, S)]  # no straight (missing T)
        rank, tb = _evaluate_five(hand)
        assert rank == HandRank.HIGH_CARD
        assert tb[0] == 14

    def test_high_card_tiebreak_all_cards(self):
        hand_k = [c(Rank.ACE, S), c(Rank.KING, H), c(Rank.QUEEN, D),
                  c(Rank.JACK, C), c(Rank.NINE, S)]
        hand_8 = [c(Rank.ACE, H), c(Rank.KING, D), c(Rank.QUEEN, C),
                  c(Rank.JACK, S), c(Rank.EIGHT, H)]
        r1, tb1 = _evaluate_five(hand_k)
        r2, tb2 = _evaluate_five(hand_8)
        assert r1 == r2 == HandRank.HIGH_CARD
        assert (r1, tb1) > (r2, tb2)

    def test_high_card_not_flush(self):
        """5 cards of different suits and no pair is high card."""
        hand = [c(Rank.ACE, S), c(Rank.NINE, H), c(Rank.SEVEN, D),
                c(Rank.FIVE, C), c(Rank.TWO, S)]
        rank, _ = _evaluate_five(hand)
        assert rank == HandRank.HIGH_CARD

    # ── Hand Ranking Order ────────────────────────────────────────────────────

    def test_hand_ranking_order(self):
        """Verify the numeric ordering of hand ranks."""
        assert HandRank.HIGH_CARD < HandRank.ONE_PAIR
        assert HandRank.ONE_PAIR < HandRank.TWO_PAIR
        assert HandRank.TWO_PAIR < HandRank.THREE_OF_A_KIND
        assert HandRank.THREE_OF_A_KIND < HandRank.STRAIGHT
        assert HandRank.STRAIGHT < HandRank.FLUSH
        assert HandRank.FLUSH < HandRank.FULL_HOUSE
        assert HandRank.FULL_HOUSE < HandRank.FOUR_OF_A_KIND
        assert HandRank.FOUR_OF_A_KIND < HandRank.STRAIGHT_FLUSH
        assert HandRank.STRAIGHT_FLUSH < HandRank.ROYAL_FLUSH


# ─── best_hand ────────────────────────────────────────────────────────────────

class TestBestHand:
    """Tests for the 7-card (hole + community) best hand selector."""

    def test_three_aces_from_hole_pair_plus_community_ace(self):
        """
        Reported scenario: AA in hole + A in community should be Three of a Kind,
        NOT One Pair.
        """
        hole = [c(Rank.ACE, S), c(Rank.ACE, H)]
        community = [
            c(Rank.ACE, D),
            c(Rank.TWO, C),
            c(Rank.SEVEN, H),
            c(Rank.KING, S),
            c(Rank.QUEEN, D),
        ]
        rank, tb, best5 = best_hand(hole, community)
        assert rank == HandRank.THREE_OF_A_KIND, (
            f"Expected Three of a Kind, got {hand_name(rank)}"
        )
        assert tb[0] == 14  # trips are aces

    def test_three_aces_partial_board_flop(self):
        """AA hole + A on flop (5 cards total)."""
        hole = [c(Rank.ACE, S), c(Rank.ACE, H)]
        community = [c(Rank.ACE, D), c(Rank.TWO, C), c(Rank.SEVEN, H)]
        rank, tb, best5 = best_hand(hole, community)
        assert rank == HandRank.THREE_OF_A_KIND
        assert tb[0] == 14

    def test_full_house_from_trips_plus_board_pair(self):
        """AA + AKK board → Full House (aces full of kings)."""
        hole = [c(Rank.ACE, S), c(Rank.ACE, H)]
        community = [
            c(Rank.ACE, D),
            c(Rank.KING, S),
            c(Rank.KING, H),
            c(Rank.TWO, C),
            c(Rank.SEVEN, D),
        ]
        rank, tb, best5 = best_hand(hole, community)
        assert rank == HandRank.FULL_HOUSE
        assert tb[0] == 14  # trips rank
        assert tb[1] == 13  # pair rank

    def test_quads_from_hole_pair_plus_board_pair(self):
        """AA + AA board → Four of a Kind."""
        hole = [c(Rank.ACE, S), c(Rank.ACE, H)]
        community = [
            c(Rank.ACE, D),
            c(Rank.ACE, C),
            c(Rank.KING, S),
            c(Rank.TWO, H),
            c(Rank.THREE, D),
        ]
        rank, tb, best5 = best_hand(hole, community)
        assert rank == HandRank.FOUR_OF_A_KIND
        assert tb[0] == 14

    def test_royal_flush_with_extra_cards(self):
        """Best hand selects royal flush even with 7 cards."""
        hole = [c(Rank.ACE, S), c(Rank.KING, S)]
        community = [
            c(Rank.QUEEN, S),
            c(Rank.JACK, S),
            c(Rank.TEN, S),
            c(Rank.TWO, H),
            c(Rank.THREE, C),
        ]
        rank, tb, best5 = best_hand(hole, community)
        assert rank == HandRank.ROYAL_FLUSH

    def test_best_hand_picks_flush_over_pair(self):
        """When hand has flush AND pair, flush wins."""
        hole = [c(Rank.ACE, S), c(Rank.ACE, H)]
        community = [
            c(Rank.KING, S),
            c(Rank.QUEEN, S),
            c(Rank.JACK, S),
            c(Rank.NINE, S),
            c(Rank.TWO, H),
        ]
        rank, tb, best5 = best_hand(hole, community)
        assert rank == HandRank.FLUSH

    def test_best_hand_picks_straight_over_high_card(self):
        hole = [c(Rank.NINE, S), c(Rank.EIGHT, H)]
        community = [
            c(Rank.SEVEN, D),
            c(Rank.SIX, C),
            c(Rank.FIVE, S),
            c(Rank.ACE, H),
            c(Rank.KING, D),
        ]
        rank, tb, best5 = best_hand(hole, community)
        assert rank == HandRank.STRAIGHT
        assert tb == [9]

    def test_wheel_straight_with_extra_cards(self):
        """A-2-3-4-5 wheel when board has higher cards too."""
        hole = [c(Rank.ACE, S), c(Rank.TWO, H)]
        community = [
            c(Rank.THREE, D),
            c(Rank.FOUR, C),
            c(Rank.FIVE, S),
            c(Rank.KING, H),
            c(Rank.QUEEN, D),
        ]
        rank, tb, best5 = best_hand(hole, community)
        assert rank == HandRank.STRAIGHT
        assert tb == [5]

    def test_two_pair_from_two_board_pairs_and_kicker(self):
        """Player uses highest two-pair from a paired board."""
        hole = [c(Rank.ACE, S), c(Rank.TWO, H)]
        community = [
            c(Rank.ACE, D),
            c(Rank.KING, S),
            c(Rank.KING, H),
            c(Rank.QUEEN, C),
            c(Rank.JACK, D),
        ]
        rank, tb, best5 = best_hand(hole, community)
        assert rank == HandRank.TWO_PAIR
        assert tb[0] == 14  # aces
        assert tb[1] == 13  # kings

    def test_best_hand_returns_5_cards(self):
        hole = [c(Rank.ACE, S), c(Rank.KING, H)]
        community = [
            c(Rank.QUEEN, D),
            c(Rank.JACK, C),
            c(Rank.TEN, S),
            c(Rank.TWO, H),
            c(Rank.THREE, D),
        ]
        rank, tb, best5 = best_hand(hole, community)
        assert len(best5) == 5

    def test_best_hand_cards_are_subset_of_all_cards(self):
        hole = [c(Rank.ACE, S), c(Rank.KING, H)]
        community = [
            c(Rank.QUEEN, D),
            c(Rank.JACK, C),
            c(Rank.TEN, S),
            c(Rank.TWO, H),
            c(Rank.THREE, D),
        ]
        rank, tb, best5 = best_hand(hole, community)
        all_cards = set(hole + community)
        for card in best5:
            assert card in all_cards

    def test_best_hand_with_five_cards_only(self):
        """When only 5 cards total (flop scenario), returns the one combo."""
        hole = [c(Rank.ACE, S), c(Rank.ACE, H)]
        community = [c(Rank.ACE, D), c(Rank.TWO, C), c(Rank.SEVEN, H)]
        rank, tb, best5 = best_hand(hole, community)
        assert rank == HandRank.THREE_OF_A_KIND

    def test_best_hand_with_six_cards(self):
        """Turn scenario: 2 hole + 4 community = 6 cards."""
        hole = [c(Rank.ACE, S), c(Rank.ACE, H)]
        community = [c(Rank.ACE, D), c(Rank.TWO, C), c(Rank.SEVEN, H), c(Rank.KING, S)]
        rank, tb, best5 = best_hand(hole, community)
        assert rank == HandRank.THREE_OF_A_KIND

    def test_tiebreak_selects_higher_rank_in_straight(self):
        """Higher straight beats lower straight on the same board.
        hole_hi: 9-8 + community 5-6-7 → 5-6-7-8-9 straight (9-high)
        hole_lo: 3-4 + community 5-6-7 → 3-4-5-6-7 straight (7-high)
        """
        community = [
            c(Rank.FIVE, D),
            c(Rank.SIX, C),
            c(Rank.SEVEN, S),
            c(Rank.KING, H),
            c(Rank.QUEEN, D),
        ]
        hole_hi = [c(Rank.NINE, S), c(Rank.EIGHT, H)]
        hole_lo = [c(Rank.THREE, S), c(Rank.FOUR, H)]
        r_hi, tb_hi, _ = best_hand(hole_hi, community)
        r_lo, tb_lo, _ = best_hand(hole_lo, community)
        assert r_hi == HandRank.STRAIGHT, f"hole_hi got {hand_name(r_hi)}"
        assert r_lo == HandRank.STRAIGHT, f"hole_lo got {hand_name(r_lo)}"
        assert tb_hi == [9]
        assert tb_lo == [7]
        assert (r_hi, tb_hi) > (r_lo, tb_lo)

    def test_same_hand_rank_same_tiebreak_is_equal(self):
        """Identical best hands (different suits) compare as equal."""
        hole1 = [c(Rank.ACE, S), c(Rank.KING, H)]
        hole2 = [c(Rank.ACE, H), c(Rank.KING, S)]
        community = [
            c(Rank.QUEEN, D),
            c(Rank.JACK, C),
            c(Rank.TEN, S),
            c(Rank.TWO, H),
            c(Rank.THREE, D),
        ]
        r1, tb1, _ = best_hand(hole1, community)
        r2, tb2, _ = best_hand(hole2, community)
        assert r1 == r2
        assert tb1 == tb2


# ─── hand_name ────────────────────────────────────────────────────────────────

class TestHandName:
    def test_all_ranks_have_names(self):
        for rank_val, name in HAND_NAMES.items():
            assert hand_name(rank_val) == name

    def test_unknown_rank_returns_unknown(self):
        assert hand_name(99) == "Unknown"

    def test_royal_flush_name(self):
        assert hand_name(HandRank.ROYAL_FLUSH) == "Royal Flush"

    def test_high_card_name(self):
        assert hand_name(HandRank.HIGH_CARD) == "High Card"


# ─── hand_strength ────────────────────────────────────────────────────────────

class TestHandStrength:
    """Monte Carlo equity estimator — tests check statistical properties."""

    def test_aces_preflop_stronger_than_random(self):
        """Pocket aces should have equity > 0.5 against random hands."""
        import random
        random.seed(42)
        hole = [c(Rank.ACE, S), c(Rank.ACE, H)]
        strength = hand_strength(hole, [])
        assert strength > 0.5, f"AA preflop equity {strength:.3f} should be > 0.5"

    def test_aces_preflop_much_stronger_than_sevens(self):
        """AA should have significantly higher equity than 7-2 offsuit."""
        import random
        random.seed(42)
        aa_strength = hand_strength([c(Rank.ACE, S), c(Rank.ACE, H)], [])
        random.seed(42)
        trash_strength = hand_strength([c(Rank.SEVEN, S), c(Rank.TWO, H)], [])
        assert aa_strength > trash_strength + 0.3

    def test_made_flush_on_river_near_certain(self):
        """A completed nut flush with no board pairs should have high equity."""
        import random
        random.seed(42)
        hole = [c(Rank.ACE, S), c(Rank.KING, S)]
        community = [
            c(Rank.QUEEN, S),
            c(Rank.JACK, S),
            c(Rank.NINE, S),
            c(Rank.TWO, H),
            c(Rank.THREE, D),
        ]
        strength = hand_strength(hole, community)
        # Nut flush with no pairing board — should win nearly always
        assert strength > 0.85, f"Nut flush equity {strength:.3f} should be > 0.85"

    def test_returns_float_between_0_and_1(self):
        import random
        random.seed(0)
        hole = [c(Rank.TEN, S), c(Rank.FIVE, H)]
        strength = hand_strength(hole, [])
        assert 0.0 <= strength <= 1.0

    def test_with_community_cards(self):
        import random
        random.seed(0)
        hole = [c(Rank.ACE, S), c(Rank.KING, H)]
        community = [c(Rank.ACE, D), c(Rank.KING, C), c(Rank.TWO, H)]
        strength = hand_strength(hole, community)
        # Top two pair on flop should be strong
        assert strength > 0.6


# ─── pot_odds ─────────────────────────────────────────────────────────────────

class TestPotOdds:
    def test_zero_call_returns_zero(self):
        assert pot_odds(0, 100) == 0.0

    def test_negative_call_returns_zero(self):
        assert pot_odds(-10, 100) == 0.0

    def test_call_equal_to_pot(self):
        """Calling an amount equal to the pot = 50% pot odds."""
        odds = pot_odds(100, 100)
        assert abs(odds - 0.5) < 1e-9

    def test_small_call_relative_to_pot(self):
        """Calling 10 into a 90 pot: need 10/100 = 10% equity to break even."""
        odds = pot_odds(10, 90)
        assert abs(odds - 0.10) < 1e-9

    def test_large_call_relative_to_pot(self):
        """Calling 90 into a 10 pot: need 90/100 = 90% equity."""
        odds = pot_odds(90, 10)
        assert abs(odds - 0.90) < 1e-9

    def test_result_between_0_and_1(self):
        for call_amount in [1, 50, 100, 500]:
            for pot_size in [1, 50, 100, 500]:
                result = pot_odds(call_amount, pot_size)
                assert 0.0 <= result <= 1.0

    def test_larger_call_means_higher_required_equity(self):
        """The more you have to call relative to the pot, the higher equity you need."""
        small = pot_odds(10, 100)
        large = pot_odds(80, 100)
        assert large > small
