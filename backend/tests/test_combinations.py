from game.combinations import can_play_on, detect_combination
from game.models import Card, CombinationType, SpecialType, Suit


def make_card(rank: int, suit: str = "jade") -> Card:
    return Card(suit=Suit(suit), rank=rank)


def phoenix() -> Card:
    return Card(suit=Suit.SPECIAL, special=SpecialType.PHOENIX)


def dragon() -> Card:
    return Card(suit=Suit.SPECIAL, special=SpecialType.DRAGON)


def hound() -> Card:
    return Card(suit=Suit.SPECIAL, special=SpecialType.HOUND)


def mah_jong() -> Card:
    return Card(suit=Suit.SPECIAL, special=SpecialType.MAH_JONG)


# ── Singles ──────────────────────────────────────────────────────────


class TestSingles:
    def test_normal_card(self):
        combo = detect_combination([make_card(7)])
        assert combo.type == CombinationType.SINGLE
        assert combo.rank == 7.0

    def test_ace(self):
        combo = detect_combination([make_card(14)])
        assert combo.type == CombinationType.SINGLE
        assert combo.rank == 14.0

    def test_dragon(self):
        combo = detect_combination([dragon()])
        assert combo.type == CombinationType.SINGLE
        assert combo.rank == 15.0

    def test_phoenix(self):
        combo = detect_combination([phoenix()])
        assert combo.type == CombinationType.SINGLE
        assert combo.rank == 14.5

    def test_mah_jong(self):
        combo = detect_combination([mah_jong()])
        assert combo.type == CombinationType.SINGLE
        assert combo.rank == 1.0

    def test_hound(self):
        combo = detect_combination([hound()])
        assert combo.type == CombinationType.HOUND_LEAD
        assert combo.rank == 0

    def test_empty_returns_none(self):
        assert detect_combination([]) is None


# ── Pairs ────────────────────────────────────────────────────────────


class TestPairs:
    def test_normal_pair(self):
        combo = detect_combination([make_card(7, "jade"), make_card(7, "sword")])
        assert combo.type == CombinationType.PAIR
        assert combo.rank == 7.0

    def test_phoenix_pair(self):
        combo = detect_combination([make_card(9, "jade"), phoenix()])
        assert combo.type == CombinationType.PAIR
        assert combo.rank == 9.0

    def test_different_ranks_invalid(self):
        assert detect_combination([make_card(7), make_card(8)]) is None

    def test_dragon_cannot_pair(self):
        assert detect_combination([dragon(), make_card(14)]) is None

    def test_hound_cannot_pair(self):
        assert detect_combination([hound(), make_card(5)]) is None

    def test_mah_jong_cannot_pair(self):
        assert detect_combination([mah_jong(), make_card(2)]) is None

    def test_phoenix_dragon_invalid(self):
        assert detect_combination([phoenix(), dragon()]) is None

    def test_phoenix_mah_jong_invalid(self):
        assert detect_combination([phoenix(), mah_jong()]) is None


# ── Triples ──────────────────────────────────────────────────────────


class TestTriples:
    def test_normal_triple(self):
        combo = detect_combination([
            make_card(5, "jade"), make_card(5, "sword"), make_card(5, "pagoda"),
        ])
        assert combo.type == CombinationType.TRIPLE
        assert combo.rank == 5.0

    def test_phoenix_triple(self):
        combo = detect_combination([
            make_card(8, "jade"), make_card(8, "sword"), phoenix(),
        ])
        assert combo.type == CombinationType.TRIPLE
        assert combo.rank == 8.0

    def test_three_different_ranks_invalid(self):
        assert detect_combination([
            make_card(3), make_card(4), make_card(5),
        ]) is None

    def test_mah_jong_cannot_triple(self):
        assert detect_combination([
            mah_jong(), make_card(2, "jade"), make_card(2, "sword"),
        ]) is None


# ── Full House ───────────────────────────────────────────────────────


class TestFullHouse:
    def test_normal_full_house(self):
        combo = detect_combination([
            make_card(7, "jade"), make_card(7, "sword"), make_card(7, "pagoda"),
            make_card(3, "jade"), make_card(3, "sword"),
        ])
        assert combo.type == CombinationType.FULL_HOUSE
        assert combo.rank == 7.0

    def test_trio_rank_determines_comparison(self):
        combo = detect_combination([
            make_card(4, "jade"), make_card(4, "sword"), make_card(4, "pagoda"),
            make_card(14, "jade"), make_card(14, "sword"),
        ])
        assert combo.rank == 4.0

    def test_phoenix_with_two_pairs(self):
        combo = detect_combination([
            make_card(5, "jade"), make_card(5, "sword"),
            make_card(9, "jade"), make_card(9, "sword"),
            phoenix(),
        ])
        assert combo.type == CombinationType.FULL_HOUSE
        assert combo.rank == 9.0  # phoenix joins higher pair

    def test_phoenix_with_trio_and_singleton(self):
        combo = detect_combination([
            make_card(10, "jade"), make_card(10, "sword"), make_card(10, "pagoda"),
            make_card(3, "jade"),
            phoenix(),
        ])
        assert combo.type == CombinationType.FULL_HOUSE
        assert combo.rank == 10.0

    def test_mah_jong_cannot_full_house(self):
        assert detect_combination([
            mah_jong(),
            make_card(5, "jade"), make_card(5, "sword"), make_card(5, "pagoda"),
            make_card(3, "jade"),
        ]) is None

    def test_four_of_rank_plus_one_invalid(self):
        assert detect_combination([
            make_card(8, "jade"), make_card(8, "sword"),
            make_card(8, "pagoda"), make_card(8, "star"),
            make_card(3, "jade"),
        ]) is None


# ── Pair Sequences ───────────────────────────────────────────────────


class TestPairSequences:
    def test_two_consecutive_pairs(self):
        combo = detect_combination([
            make_card(3, "jade"), make_card(3, "sword"),
            make_card(4, "jade"), make_card(4, "sword"),
        ])
        assert combo.type == CombinationType.PAIR_SEQUENCE
        assert combo.rank == 4.0
        assert combo.length == 2

    def test_three_consecutive_pairs(self):
        combo = detect_combination([
            make_card(5, "jade"), make_card(5, "sword"),
            make_card(6, "jade"), make_card(6, "sword"),
            make_card(7, "jade"), make_card(7, "sword"),
        ])
        assert combo.type == CombinationType.PAIR_SEQUENCE
        assert combo.rank == 7.0
        assert combo.length == 3

    def test_non_consecutive_pairs_invalid(self):
        assert detect_combination([
            make_card(3, "jade"), make_card(3, "sword"),
            make_card(5, "jade"), make_card(5, "sword"),
        ]) is None

    def test_phoenix_fills_missing_card(self):
        combo = detect_combination([
            make_card(6, "jade"), make_card(6, "sword"),
            make_card(7, "jade"),
            phoenix(),
        ])
        assert combo.type == CombinationType.PAIR_SEQUENCE
        assert combo.rank == 7.0
        assert combo.length == 2

    def test_phoenix_three_pair_sequence(self):
        combo = detect_combination([
            make_card(3, "jade"), make_card(3, "sword"),
            make_card(4, "jade"),
            make_card(5, "jade"), make_card(5, "sword"),
            phoenix(),
        ])
        assert combo.type == CombinationType.PAIR_SEQUENCE
        assert combo.rank == 5.0
        assert combo.length == 3

    def test_mah_jong_cannot_pair_sequence(self):
        assert detect_combination([
            mah_jong(), make_card(2, "jade"),
            make_card(3, "jade"), make_card(3, "sword"),
        ]) is None

    def test_odd_card_count_invalid(self):
        assert detect_combination([
            make_card(3, "jade"), make_card(3, "sword"),
            make_card(4, "jade"), make_card(4, "sword"),
            make_card(5, "jade"),
        ]) is None


# ── Straights ────────────────────────────────────────────────────────


class TestStraights:
    def test_five_card_straight(self):
        combo = detect_combination([
            make_card(3, "jade"), make_card(4, "sword"),
            make_card(5, "pagoda"), make_card(6, "star"),
            make_card(7, "jade"),
        ])
        assert combo.type == CombinationType.STRAIGHT
        assert combo.rank == 7.0
        assert combo.length == 5

    def test_seven_card_straight(self):
        combo = detect_combination([
            make_card(4, "jade"), make_card(5, "sword"),
            make_card(6, "pagoda"), make_card(7, "star"),
            make_card(8, "jade"), make_card(9, "sword"),
            make_card(10, "pagoda"),
        ])
        assert combo.type == CombinationType.STRAIGHT
        assert combo.rank == 10.0
        assert combo.length == 7

    def test_mah_jong_as_rank_one(self):
        combo = detect_combination([
            mah_jong(),
            make_card(2, "jade"), make_card(3, "sword"),
            make_card(4, "pagoda"), make_card(5, "star"),
        ])
        assert combo.type == CombinationType.STRAIGHT
        assert combo.rank == 5.0
        assert combo.length == 5

    def test_phoenix_fills_gap(self):
        combo = detect_combination([
            make_card(3, "jade"), make_card(4, "sword"),
            make_card(6, "pagoda"), make_card(7, "star"),
            phoenix(),
        ])
        assert combo.type == CombinationType.STRAIGHT
        assert combo.rank == 7.0
        assert combo.length == 5

    def test_phoenix_extends_at_top(self):
        combo = detect_combination([
            make_card(10, "jade"), make_card(11, "sword"),
            make_card(12, "pagoda"), make_card(13, "star"),
            phoenix(),
        ])
        assert combo.type == CombinationType.STRAIGHT
        assert combo.rank == 14.0
        assert combo.length == 5

    def test_phoenix_extends_ace_high(self):
        # 11-12-13-14-Phoenix: cannot go above 14, extends at bottom (10)
        combo = detect_combination([
            make_card(11, "jade"), make_card(12, "sword"),
            make_card(13, "pagoda"), make_card(14, "star"),
            phoenix(),
        ])
        assert combo.type == CombinationType.STRAIGHT
        assert combo.rank == 14.0
        assert combo.length == 5

    def test_mah_jong_and_phoenix_in_straight(self):
        combo = detect_combination([
            mah_jong(),
            make_card(2, "jade"), make_card(3, "sword"),
            make_card(5, "pagoda"),
            phoenix(),
        ])
        assert combo.type == CombinationType.STRAIGHT
        assert combo.rank == 5.0
        assert combo.length == 5

    def test_four_cards_too_short(self):
        assert detect_combination([
            make_card(3, "jade"), make_card(4, "sword"),
            make_card(5, "pagoda"), make_card(6, "star"),
        ]) is None

    def test_non_consecutive_invalid(self):
        assert detect_combination([
            make_card(3, "jade"), make_card(4, "sword"),
            make_card(5, "pagoda"), make_card(6, "star"),
            make_card(8, "jade"),
        ]) is None

    def test_dragon_cannot_be_in_straight(self):
        assert detect_combination([
            make_card(11, "jade"), make_card(12, "sword"),
            make_card(13, "pagoda"), make_card(14, "star"),
            dragon(),
        ]) is None

    def test_hound_cannot_be_in_straight(self):
        assert detect_combination([
            make_card(3, "jade"), make_card(4, "sword"),
            make_card(5, "pagoda"), make_card(6, "star"),
            hound(),
        ]) is None

    def test_duplicate_rank_in_straight_invalid(self):
        assert detect_combination([
            make_card(3, "jade"), make_card(3, "sword"),
            make_card(4, "pagoda"), make_card(5, "star"),
            make_card(6, "jade"),
        ]) is None

    def test_full_fourteen_card_straight(self):
        cards = [mah_jong()] + [make_card(r, "jade") for r in range(2, 15)]
        combo = detect_combination(cards)
        assert combo.type == CombinationType.STRAIGHT
        assert combo.rank == 14.0
        assert combo.length == 14


# ── Four Bombs ───────────────────────────────────────────────────────


class TestFourBombs:
    def test_four_of_a_kind(self):
        combo = detect_combination([
            make_card(9, "jade"), make_card(9, "sword"),
            make_card(9, "pagoda"), make_card(9, "star"),
        ])
        assert combo.type == CombinationType.FOUR_BOMB
        assert combo.rank == 9.0
        assert combo.is_bomb

    def test_phoenix_cannot_be_in_bomb(self):
        assert detect_combination([
            make_card(9, "jade"), make_card(9, "sword"),
            make_card(9, "pagoda"), phoenix(),
        ]) is None

    def test_three_of_kind_plus_different_invalid(self):
        # 3 nines + a ten: not a bomb, not a valid 4-card play
        assert detect_combination([
            make_card(9, "jade"), make_card(9, "sword"),
            make_card(9, "pagoda"), make_card(10, "star"),
        ]) is None


# ── Straight Bombs ───────────────────────────────────────────────────


class TestStraightBombs:
    def test_five_card_same_suit_consecutive(self):
        combo = detect_combination([
            make_card(3, "jade"), make_card(4, "jade"),
            make_card(5, "jade"), make_card(6, "jade"),
            make_card(7, "jade"),
        ])
        assert combo.type == CombinationType.STRAIGHT_BOMB
        assert combo.rank == 7.0
        assert combo.length == 5
        assert combo.is_bomb

    def test_six_card_straight_bomb(self):
        combo = detect_combination([
            make_card(5, "sword"), make_card(6, "sword"),
            make_card(7, "sword"), make_card(8, "sword"),
            make_card(9, "sword"), make_card(10, "sword"),
        ])
        assert combo.type == CombinationType.STRAIGHT_BOMB
        assert combo.rank == 10.0
        assert combo.length == 6
        assert combo.is_bomb

    def test_mixed_suits_is_straight_not_bomb(self):
        combo = detect_combination([
            make_card(3, "jade"), make_card(4, "sword"),
            make_card(5, "jade"), make_card(6, "jade"),
            make_card(7, "jade"),
        ])
        assert combo.type == CombinationType.STRAIGHT
        assert not combo.is_bomb

    def test_same_suit_not_consecutive_invalid(self):
        assert detect_combination([
            make_card(3, "jade"), make_card(4, "jade"),
            make_card(5, "jade"), make_card(6, "jade"),
            make_card(8, "jade"),
        ]) is None

    def test_four_same_suit_consecutive_not_straight_bomb(self):
        # 4 cards same suit consecutive: treated as pair sequence check fails (odd pairs),
        # not enough for straight, so should be None
        assert detect_combination([
            make_card(3, "jade"), make_card(4, "jade"),
            make_card(5, "jade"), make_card(6, "jade"),
        ]) is None

    def test_phoenix_prevents_straight_bomb(self):
        combo = detect_combination([
            make_card(3, "jade"), make_card(4, "jade"),
            make_card(5, "jade"), make_card(6, "jade"),
            phoenix(),
        ])
        assert combo is not None
        assert combo.type == CombinationType.STRAIGHT
        assert not combo.is_bomb

    def test_mah_jong_prevents_straight_bomb(self):
        # Mah Jong is suit SPECIAL, so the straight is not all one suit
        combo = detect_combination([
            mah_jong(),
            make_card(2, "jade"), make_card(3, "jade"),
            make_card(4, "jade"), make_card(5, "jade"),
        ])
        assert combo.type == CombinationType.STRAIGHT
        assert not combo.is_bomb


# ── Invalid Combinations ─────────────────────────────────────────────


class TestInvalid:
    def test_random_cards(self):
        assert detect_combination([
            make_card(3), make_card(5), make_card(7),
        ]) is None

    def test_hound_with_other_card(self):
        assert detect_combination([hound(), make_card(5)]) is None

    def test_dragon_with_other_card(self):
        assert detect_combination([dragon(), make_card(5)]) is None

    def test_two_specials(self):
        assert detect_combination([dragon(), hound()]) is None


# ── can_play_on ──────────────────────────────────────────────────────


class TestCanPlayOn:
    def test_leading_any_combination(self):
        combo = detect_combination([make_card(5)])
        assert can_play_on(combo, None)

    def test_higher_single_beats_lower(self):
        low = detect_combination([make_card(5)])
        high = detect_combination([make_card(10)])
        assert can_play_on(high, low)
        assert not can_play_on(low, high)

    def test_higher_pair_beats_lower(self):
        low = detect_combination([make_card(3, "jade"), make_card(3, "sword")])
        high = detect_combination([make_card(10, "jade"), make_card(10, "sword")])
        assert can_play_on(high, low)
        assert not can_play_on(low, high)

    def test_same_type_different_length_fails(self):
        five = detect_combination([
            make_card(3, "jade"), make_card(4, "sword"),
            make_card(5, "pagoda"), make_card(6, "star"),
            make_card(7, "jade"),
        ])
        seven = detect_combination([
            make_card(3, "jade"), make_card(4, "sword"),
            make_card(5, "pagoda"), make_card(6, "star"),
            make_card(7, "jade"), make_card(8, "sword"),
            make_card(9, "pagoda"),
        ])
        assert not can_play_on(five, seven)
        assert not can_play_on(seven, five)

    def test_bomb_beats_non_bomb(self):
        single = detect_combination([make_card(14)])
        bomb = detect_combination([
            make_card(5, "jade"), make_card(5, "sword"),
            make_card(5, "pagoda"), make_card(5, "star"),
        ])
        assert can_play_on(bomb, single)
        assert not can_play_on(single, bomb)

    def test_phoenix_single_cannot_beat_dragon(self):
        ph = detect_combination([phoenix()])
        dr = detect_combination([dragon()])
        assert not can_play_on(ph, dr)

    def test_phoenix_single_beats_ace(self):
        ph = detect_combination([phoenix()])
        ace = detect_combination([make_card(14)])
        assert can_play_on(ph, ace)

    def test_hound_lead_cannot_play_on_trick(self):
        h = detect_combination([hound()])
        single = detect_combination([make_card(5)])
        assert not can_play_on(h, single)

    def test_hound_lead_can_lead(self):
        h = detect_combination([hound()])
        assert can_play_on(h, None)

    def test_different_types_fail(self):
        single = detect_combination([make_card(14)])
        pair = detect_combination([make_card(3, "jade"), make_card(3, "sword")])
        assert not can_play_on(single, pair)

    def test_straight_bomb_beats_four_bomb(self):
        four = detect_combination([
            make_card(14, "jade"), make_card(14, "sword"),
            make_card(14, "pagoda"), make_card(14, "star"),
        ])
        straight = detect_combination([
            make_card(3, "jade"), make_card(4, "jade"),
            make_card(5, "jade"), make_card(6, "jade"),
            make_card(7, "jade"),
        ])
        assert can_play_on(straight, four)
        assert not can_play_on(four, straight)

    def test_full_house_trio_rank_comparison(self):
        low = detect_combination([
            make_card(4, "jade"), make_card(4, "sword"), make_card(4, "pagoda"),
            make_card(14, "jade"), make_card(14, "sword"),
        ])
        high = detect_combination([
            make_card(10, "jade"), make_card(10, "sword"), make_card(10, "pagoda"),
            make_card(2, "jade"), make_card(2, "sword"),
        ])
        assert can_play_on(high, low)
        assert not can_play_on(low, high)

    def test_pair_sequence_same_length_higher_rank(self):
        low = detect_combination([
            make_card(3, "jade"), make_card(3, "sword"),
            make_card(4, "jade"), make_card(4, "sword"),
        ])
        high = detect_combination([
            make_card(8, "jade"), make_card(8, "sword"),
            make_card(9, "jade"), make_card(9, "sword"),
        ])
        assert can_play_on(high, low)
        assert not can_play_on(low, high)
