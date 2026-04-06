import random

from game.deck import create_deck, deal, shuffle_deck
from game.models import SpecialType, Suit


class TestCreateDeck:
    def test_deck_size(self):
        deck = create_deck()
        assert len(deck) == 56

    def test_normal_cards_count(self):
        deck = create_deck()
        normal = [c for c in deck if not c.is_special]
        assert len(normal) == 52

    def test_special_cards_count(self):
        deck = create_deck()
        specials = [c for c in deck if c.is_special]
        assert len(specials) == 4

    def test_all_special_types_present(self):
        deck = create_deck()
        special_types = {c.special for c in deck if c.is_special}
        assert special_types == set(SpecialType)

    def test_four_suits_thirteen_ranks(self):
        deck = create_deck()
        normal = [c for c in deck if not c.is_special]
        suits = {c.suit for c in normal}
        assert suits == {Suit.JADE, Suit.SWORD, Suit.PAGODA, Suit.STAR}
        for suit in suits:
            ranks = sorted(c.rank for c in normal if c.suit == suit)
            assert ranks == list(range(2, 15))

    def test_no_duplicates(self):
        deck = create_deck()
        assert len(set(deck)) == 56


class TestShuffleDeck:
    def test_preserves_all_cards(self):
        deck = create_deck()
        shuffled = shuffle_deck(deck, rng=random.Random(42))
        assert sorted(deck, key=lambda c: (c.suit, c.rank or 0, c.special or "")) == \
               sorted(shuffled, key=lambda c: (c.suit, c.rank or 0, c.special or ""))

    def test_deterministic_with_seed(self):
        deck = create_deck()
        a = shuffle_deck(deck, rng=random.Random(42))
        b = shuffle_deck(deck, rng=random.Random(42))
        assert a == b

    def test_different_order(self):
        deck = create_deck()
        shuffled = shuffle_deck(deck, rng=random.Random(42))
        assert deck != shuffled

    def test_does_not_mutate_original(self):
        deck = create_deck()
        original = list(deck)
        shuffle_deck(deck, rng=random.Random(42))
        assert deck == original


class TestDeal:
    def test_four_hands_of_fourteen(self):
        deck = create_deck()
        hands = deal(deck)
        assert len(hands) == 4
        for hand in hands:
            assert len(hand) == 14

    def test_all_cards_distributed(self):
        deck = create_deck()
        hands = deal(deck)
        all_dealt = []
        for hand in hands:
            all_dealt.extend(hand)
        assert len(all_dealt) == 56
        assert set(all_dealt) == set(deck)

    def test_no_card_in_multiple_hands(self):
        deck = create_deck()
        hands = deal(deck)
        all_dealt = []
        for hand in hands:
            all_dealt.extend(hand)
        assert len(all_dealt) == len(set(all_dealt))
