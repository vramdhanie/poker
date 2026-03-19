"""Tests for cards.py — Card, Deck, and formatting utilities."""

import pytest
from poker.cards import (
    Card, Deck, Rank, Suit,
    SUIT_ICONS, RANK_NAMES, RESET,
    format_hand, format_community, HIDDEN_CARD,
)


# ─── Card ─────────────────────────────────────────────────────────────────────

class TestCard:
    def test_str_contains_rank_and_suit(self):
        c = Card(Rank.ACE, Suit.SPADES)
        s = str(c)
        assert "A" in s
        assert "♠" in s

    def test_str_contains_ansi_reset(self):
        c = Card(Rank.KING, Suit.HEARTS)
        assert RESET in str(c)

    def test_plain_no_ansi(self):
        c = Card(Rank.ACE, Suit.SPADES)
        plain = c.plain()
        assert "\033" not in plain
        assert plain == "A♠"

    def test_repr(self):
        c = Card(Rank.TWO, Suit.CLUBS)
        assert "2" in repr(c)
        assert "♣" in repr(c)

    def test_equality(self):
        assert Card(Rank.ACE, Suit.SPADES) == Card(Rank.ACE, Suit.SPADES)
        assert Card(Rank.ACE, Suit.SPADES) != Card(Rank.ACE, Suit.HEARTS)
        assert Card(Rank.ACE, Suit.SPADES) != Card(Rank.KING, Suit.SPADES)

    def test_hashable(self):
        """Cards must be hashable to be used in sets (used by hand_strength)."""
        c1 = Card(Rank.ACE, Suit.SPADES)
        c2 = Card(Rank.KING, Suit.HEARTS)
        s = {c1, c2}
        assert len(s) == 2
        assert c1 in s

    def test_frozen(self):
        c = Card(Rank.ACE, Suit.SPADES)
        with pytest.raises(AttributeError):
            c.rank = Rank.KING  # type: ignore[misc]

    def test_all_suits_have_icons(self):
        for suit in Suit:
            c = Card(Rank.ACE, suit)
            assert SUIT_ICONS[suit] in str(c)

    def test_all_ranks_have_names(self):
        for rank in Rank:
            c = Card(rank, Suit.SPADES)
            assert RANK_NAMES[rank] in str(c)

    def test_red_suits(self):
        """Hearts and diamonds should use red ANSI codes."""
        for suit in (Suit.HEARTS, Suit.DIAMONDS):
            c = Card(Rank.ACE, suit)
            assert "\033[91m" in str(c)

    def test_black_suits(self):
        """Clubs and spades should use white/grey ANSI codes."""
        for suit in (Suit.CLUBS, Suit.SPADES):
            c = Card(Rank.ACE, suit)
            assert "\033[37m" in str(c)


# ─── Deck ─────────────────────────────────────────────────────────────────────

class TestDeck:
    def test_deck_has_52_cards(self):
        d = Deck()
        assert len(d) == 52

    def test_deck_has_all_unique_cards(self):
        d = Deck()
        # Deal all 52 cards and check uniqueness
        all_cards = d.deal(52)
        assert len(set(all_cards)) == 52

    def test_deck_covers_all_ranks_and_suits(self):
        d = Deck()
        all_cards = d.deal(52)
        for rank in Rank:
            for suit in Suit:
                assert Card(rank, suit) in all_cards

    def test_deal_reduces_deck_size(self):
        d = Deck()
        d.deal(5)
        assert len(d) == 47

    def test_deal_one(self):
        d = Deck()
        c = d.deal_one()
        assert isinstance(c, Card)
        assert len(d) == 51

    def test_deal_returns_correct_count(self):
        d = Deck()
        cards = d.deal(7)
        assert len(cards) == 7

    def test_deal_too_many_raises(self):
        d = Deck()
        with pytest.raises(ValueError):
            d.deal(53)

    def test_shuffle_changes_order(self):
        """Shuffling should (with overwhelming probability) change card order."""
        import random
        random.seed(42)
        d1 = Deck()
        cards_before = d1.deal(52)

        random.seed(42)
        d2 = Deck()
        d2.shuffle()
        cards_after = d2.deal(52)

        # With 52! possible orderings, same order is astronomically unlikely
        assert cards_before != cards_after

    def test_shuffle_preserves_all_cards(self):
        d = Deck()
        d.shuffle()
        all_cards = d.deal(52)
        assert len(set(all_cards)) == 52

    def test_sequential_deals_do_not_repeat_cards(self):
        d = Deck()
        d.shuffle()
        first = d.deal(10)
        second = d.deal(10)
        assert not set(first) & set(second)


# ─── Formatting ───────────────────────────────────────────────────────────────

class TestFormatHand:
    def test_empty_hand(self):
        assert format_hand([]) == "[ ]"

    def test_single_card_visible(self):
        c = Card(Rank.ACE, Suit.SPADES)
        result = format_hand([c])
        assert "A" in result
        assert "♠" in result

    def test_hidden_hand_hides_cards(self):
        cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
        result = format_hand(cards, hide=True)
        assert "A" not in result
        assert "K" not in result
        assert "?" in result

    def test_two_cards_formatted(self):
        cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
        result = format_hand(cards)
        assert "A" in result
        assert "K" in result


class TestFormatCommunity:
    def test_no_cards_shows_placeholders(self):
        result = format_community([])
        # 5 placeholder slots
        assert result.count("[  ]") == 5

    def test_three_cards_shows_two_placeholders(self):
        cards = [
            Card(Rank.ACE, Suit.SPADES),
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.QUEEN, Suit.DIAMONDS),
        ]
        result = format_community(cards)
        assert result.count("[  ]") == 2

    def test_five_cards_no_placeholders(self):
        cards = [
            Card(Rank.ACE, Suit.SPADES),
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.QUEEN, Suit.DIAMONDS),
            Card(Rank.JACK, Suit.CLUBS),
            Card(Rank.TEN, Suit.SPADES),
        ]
        result = format_community(cards)
        assert "[  ]" not in result
