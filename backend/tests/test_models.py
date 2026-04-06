from game.models import Card, Combination, CombinationType, SpecialType, Suit


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


class TestCard:
    def test_normal_card_creation(self):
        card = make_card(7, "jade")
        assert card.suit == Suit.JADE
        assert card.rank == 7
        assert card.special is None

    def test_special_card_creation(self):
        d = dragon()
        assert d.suit == Suit.SPECIAL
        assert d.special == SpecialType.DRAGON
        assert d.rank is None

    def test_is_special(self):
        assert dragon().is_special
        assert phoenix().is_special
        assert hound().is_special
        assert mah_jong().is_special
        assert not make_card(5).is_special

    def test_display_rank_normal(self):
        assert make_card(2).display_rank == "2"
        assert make_card(10).display_rank == "10"
        assert make_card(11).display_rank == "J"
        assert make_card(12).display_rank == "Q"
        assert make_card(13).display_rank == "K"
        assert make_card(14).display_rank == "A"

    def test_display_rank_special(self):
        assert dragon().display_rank == "dragon"
        assert phoenix().display_rank == "phoenix"
        assert hound().display_rank == "hound"
        assert mah_jong().display_rank == "mah_jong"

    def test_sort_key_ordering(self):
        cards = [dragon(), phoenix(), make_card(14), make_card(2), mah_jong(), hound()]
        sorted_cards = sorted(cards, key=lambda c: c.sort_key)
        expected_keys = [0.5, 1.0, 2.0, 14.0, 14.5, 15.0]
        assert [c.sort_key for c in sorted_cards] == expected_keys

    def test_point_value(self):
        assert dragon().point_value == 25
        assert phoenix().point_value == -25
        assert make_card(5).point_value == 5
        assert make_card(10).point_value == 10
        assert make_card(13).point_value == 10
        assert make_card(2).point_value == 0
        assert make_card(14).point_value == 0
        assert hound().point_value == 0
        assert mah_jong().point_value == 0

    def test_card_frozen(self):
        card = make_card(5)
        card2 = make_card(5)
        assert hash(card) == hash(card2)
        assert card == card2


class TestCombinationBeats:
    def _combo(self, ctype, rank, length, is_bomb=False):
        return Combination(
            type=ctype,
            cards=[],
            rank=rank,
            length=length,
            is_bomb=is_bomb,
        )

    def test_same_type_higher_rank_wins(self):
        low = self._combo(CombinationType.SINGLE, 5, 1)
        high = self._combo(CombinationType.SINGLE, 10, 1)
        assert high.beats(low)
        assert not low.beats(high)

    def test_same_type_same_rank_does_not_beat(self):
        a = self._combo(CombinationType.PAIR, 7, 1)
        b = self._combo(CombinationType.PAIR, 7, 1)
        assert not a.beats(b)

    def test_different_type_non_bomb_fails(self):
        single = self._combo(CombinationType.SINGLE, 14, 1)
        pair = self._combo(CombinationType.PAIR, 3, 1)
        assert not single.beats(pair)
        assert not pair.beats(single)

    def test_different_length_non_bomb_fails(self):
        short = self._combo(CombinationType.STRAIGHT, 9, 5)
        long = self._combo(CombinationType.STRAIGHT, 7, 7)
        assert not short.beats(long)
        assert not long.beats(short)

    def test_bomb_beats_non_bomb(self):
        bomb = self._combo(CombinationType.FOUR_BOMB, 5, 4, is_bomb=True)
        single = self._combo(CombinationType.SINGLE, 14, 1)
        assert bomb.beats(single)
        assert not single.beats(bomb)

    def test_bomb_vs_bomb_longer_wins(self):
        four = self._combo(CombinationType.FOUR_BOMB, 14, 4, is_bomb=True)
        straight = self._combo(CombinationType.STRAIGHT_BOMB, 7, 5, is_bomb=True)
        assert straight.beats(four)
        assert not four.beats(straight)

    def test_bomb_vs_bomb_same_length_higher_rank_wins(self):
        low = self._combo(CombinationType.STRAIGHT_BOMB, 9, 5, is_bomb=True)
        high = self._combo(CombinationType.STRAIGHT_BOMB, 12, 5, is_bomb=True)
        assert high.beats(low)
        assert not low.beats(high)

    def test_longer_straight_bomb_beats_shorter(self):
        five = self._combo(CombinationType.STRAIGHT_BOMB, 14, 5, is_bomb=True)
        six = self._combo(CombinationType.STRAIGHT_BOMB, 8, 6, is_bomb=True)
        assert six.beats(five)
        assert not five.beats(six)

    def test_pair_sequence_same_length_higher_rank(self):
        low = self._combo(CombinationType.PAIR_SEQUENCE, 5, 3)
        high = self._combo(CombinationType.PAIR_SEQUENCE, 8, 3)
        assert high.beats(low)

    def test_full_house_comparison_uses_rank(self):
        low = self._combo(CombinationType.FULL_HOUSE, 4, 5)
        high = self._combo(CombinationType.FULL_HOUSE, 10, 5)
        assert high.beats(low)
        assert not low.beats(high)
