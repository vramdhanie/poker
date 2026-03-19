"""Tests for player.py — Player and AIPlayer."""

import pytest
from poker.cards import Card, Rank, Suit
from poker.player import Action, Player, AIPlayer, AI_PROFILES


# ─── Helpers ──────────────────────────────────────────────────────────────────

def c(rank: Rank, suit: Suit) -> Card:
    return Card(rank, suit)

S, H, D, C = Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS


# ─── Player ───────────────────────────────────────────────────────────────────

class TestPlayer:
    def make_player(self, stack: int = 1000) -> Player:
        return Player(name="Test", stack=stack, is_human=True)

    def test_initial_state(self):
        p = self.make_player(500)
        assert p.stack == 500
        assert p.current_bet == 0
        assert p.total_bet == 0
        assert not p.folded
        assert not p.all_in

    def test_place_bet_reduces_stack(self):
        p = self.make_player(1000)
        p.place_bet(100)
        assert p.stack == 900

    def test_place_bet_increases_current_bet(self):
        p = self.make_player(1000)
        p.place_bet(100)
        assert p.current_bet == 100

    def test_place_bet_increases_total_bet(self):
        p = self.make_player(1000)
        p.place_bet(100)
        p.place_bet(50)
        assert p.total_bet == 150

    def test_place_bet_returns_actual_amount(self):
        p = self.make_player(50)
        actual = p.place_bet(100)  # more than stack
        assert actual == 50
        assert p.stack == 0

    def test_place_bet_capped_at_stack(self):
        p = self.make_player(30)
        p.place_bet(100)
        assert p.stack == 0
        assert p.current_bet == 30

    def test_place_bet_all_in_sets_flag(self):
        p = self.make_player(100)
        p.place_bet(100)
        assert p.all_in

    def test_place_bet_partial_does_not_set_all_in(self):
        p = self.make_player(100)
        p.place_bet(50)
        assert not p.all_in

    def test_can_act_normal(self):
        p = self.make_player(100)
        assert p.can_act()

    def test_can_act_folded(self):
        p = self.make_player(100)
        p.folded = True
        assert not p.can_act()

    def test_can_act_all_in(self):
        p = self.make_player(100)
        p.place_bet(100)  # goes all-in
        assert not p.can_act()

    def test_can_act_no_stack(self):
        p = self.make_player(0)
        assert not p.can_act()

    def test_reset_for_hand_clears_state(self):
        p = self.make_player(1000)
        p.hole_cards = [c(Rank.ACE, S), c(Rank.KING, H)]
        p.current_bet = 200
        p.total_bet = 200
        p.folded = True
        p.all_in = True
        p.reset_for_hand()
        assert p.hole_cards == []
        assert p.current_bet == 0
        assert p.total_bet == 0
        assert not p.folded
        assert not p.all_in

    def test_reset_for_hand_preserves_stack(self):
        p = self.make_player(750)
        p.reset_for_hand()
        assert p.stack == 750

    def test_reset_for_round_clears_current_bet_only(self):
        p = self.make_player(1000)
        p.current_bet = 100
        p.total_bet = 100
        p.reset_for_round()
        assert p.current_bet == 0
        assert p.total_bet == 100  # total_bet preserved

    def test_str_is_name(self):
        p = Player(name="Alice", stack=1000)
        assert str(p) == "Alice"

    def test_multiple_bets_accumulate_total(self):
        p = self.make_player(1000)
        p.place_bet(50)   # preflop
        p.reset_for_round()
        p.place_bet(100)  # flop
        assert p.total_bet == 150
        assert p.current_bet == 100


# ─── AIPlayer ─────────────────────────────────────────────────────────────────

class TestAIPlayer:
    def make_ai(self, profile_idx: int = 0, stack: int = 1000) -> AIPlayer:
        return AIPlayer(AI_PROFILES[profile_idx], stack=stack)

    def test_all_profiles_create_ai(self):
        for i in range(3):
            ai = self.make_ai(i)
            assert isinstance(ai, AIPlayer)
            assert ai.stack == 1000

    def test_ai_names_match_profiles(self):
        for i, profile in enumerate(AI_PROFILES):
            ai = self.make_ai(i)
            assert ai.name == profile["name"]

    def test_ai_is_not_human(self):
        ai = self.make_ai()
        assert not ai.is_human

    def test_decide_returns_action_and_amount(self):
        import random
        random.seed(42)
        ai = self.make_ai()
        ai.hole_cards = [c(Rank.ACE, S), c(Rank.ACE, H)]
        action, amount = ai.decide(
            community_cards=[],
            pot=30,
            call_amount=20,
            min_raise=40,
            max_raise=1000,
            position=1,
            street="preflop",
            num_active=4,
        )
        assert isinstance(action, Action)
        assert isinstance(amount, int)
        assert amount >= 0

    def test_decide_with_strong_hand_does_not_fold(self):
        """Pocket aces should virtually never fold preflop."""
        import random
        folds = 0
        for seed in range(20):
            random.seed(seed)
            ai = self.make_ai()
            ai.hole_cards = [c(Rank.ACE, S), c(Rank.ACE, H)]
            action, _ = ai.decide(
                community_cards=[],
                pot=30,
                call_amount=20,
                min_raise=40,
                max_raise=1000,
                position=2,
                street="preflop",
                num_active=4,
            )
            if action == Action.FOLD:
                folds += 1
        assert folds <= 2, f"AA folded {folds}/20 times preflop"

    def test_decide_with_no_call_can_check(self):
        """When call_amount is 0, AI can check."""
        import random
        checks = 0
        for seed in range(20):
            random.seed(seed)
            ai = self.make_ai()
            ai.hole_cards = [c(Rank.TWO, S), c(Rank.SEVEN, H)]
            action, _ = ai.decide(
                community_cards=[],
                pot=0,
                call_amount=0,
                min_raise=20,
                max_raise=1000,
                position=0,
                street="preflop",
                num_active=4,
            )
            # When call is 0, folding is nonsensical — should check or raise
            assert action in (Action.CHECK, Action.RAISE, Action.ALL_IN)

    def test_decide_raise_amount_within_bounds(self):
        """When AI raises, amount must be within [min_raise, max_raise]."""
        import random
        for seed in range(30):
            random.seed(seed)
            ai = self.make_ai(1)  # Bob is most aggressive
            ai.hole_cards = [c(Rank.ACE, S), c(Rank.KING, H)]
            action, amount = ai.decide(
                community_cards=[],
                pot=40,
                call_amount=0,
                min_raise=20,
                max_raise=1000,
                position=2,
                street="preflop",
                num_active=4,
            )
            if action == Action.RAISE:
                assert amount >= 20, f"Raise {amount} below min_raise 20"
                assert amount <= 1000, f"Raise {amount} above max_raise 1000"

    def test_decide_all_in_does_not_exceed_stack(self):
        """ALL_IN action amount must not exceed the player's stack."""
        import random
        random.seed(7)
        ai = self.make_ai(stack=200)
        ai.hole_cards = [c(Rank.ACE, S), c(Rank.ACE, H)]
        action, amount = ai.decide(
            community_cards=[],
            pot=1000,
            call_amount=200,
            min_raise=400,
            max_raise=200,
            position=2,
            street="preflop",
            num_active=2,
        )
        if action == Action.ALL_IN:
            assert amount <= 200

    def test_decide_call_amount_matches_parameter(self):
        """When AI calls, the returned amount equals the call_amount parameter."""
        import random
        found_call = False
        for seed in range(50):
            random.seed(seed)
            ai = self.make_ai(2)  # Carol is tight/conservative
            ai.hole_cards = [c(Rank.ACE, S), c(Rank.ACE, H)]
            action, amount = ai.decide(
                community_cards=[c(Rank.ACE, D), c(Rank.KING, C), c(Rank.QUEEN, H)],
                pot=100,
                call_amount=30,
                min_raise=60,
                max_raise=1000,
                position=1,
                street="flop",
                num_active=3,
            )
            if action == Action.CALL:
                assert amount == 30
                found_call = True
                break

    def test_all_profiles_have_required_keys(self):
        for profile in AI_PROFILES:
            assert "name" in profile
            assert "aggression" in profile
            assert "bluff_rate" in profile
            assert "tightness" in profile

    def test_profile_values_in_range(self):
        for profile in AI_PROFILES:
            assert 0.0 <= profile["aggression"] <= 1.0
            assert 0.0 <= profile["bluff_rate"] <= 1.0
            assert 0.0 <= profile["tightness"] <= 1.0

    def test_ai_inherits_player_methods(self):
        ai = self.make_ai(stack=500)
        actual = ai.place_bet(100)
        assert actual == 100
        assert ai.stack == 400
        assert ai.current_bet == 100
