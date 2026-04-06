from game.combinations import detect_combination
from game.models import (
    Card,
    Combination,
    CombinationType,
    GamePhase,
    GameState,
    Player,
    SpecialType,
    Suit,
)
from game.wish import (
    check_wish_obligation,
    clear_wish_if_fulfilled,
    set_wish,
)
from tests.conftest import dragon, hound, mah_jong, make_card, phoenix


def _make_state(
    hand: list[Card],
    active_wish: int | None = None,
    trick_combo: Combination | None = None,
) -> GameState:
    players = []
    for i in range(4):
        players.append(
            Player(
                id=f"p{i}",
                name=f"Player {i}",
                team=i % 2,
                seat=i,
                hand=hand if i == 0 else [],
            )
        )
    state = GameState(
        id="test",
        phase=GamePhase.PLAYING,
        players=players,
        active_wish=active_wish,
    )
    if trick_combo is not None:
        state.trick = [(1, trick_combo)]
    return state


class TestSetWish:
    def test_set_valid_wish(self):
        state = _make_state([])
        set_wish(state, 7)
        assert state.active_wish == 7

    def test_set_wish_clears_pending(self):
        state = _make_state([])
        state.pending_wish_from_seat = 0
        set_wish(state, 10)
        assert state.pending_wish_from_seat is None

    def test_invalid_wish_rank_too_low(self):
        state = _make_state([])
        try:
            set_wish(state, 1)
            assert False, "Should have raised"
        except ValueError:
            pass

    def test_invalid_wish_rank_too_high(self):
        state = _make_state([])
        try:
            set_wish(state, 15)
            assert False, "Should have raised"
        except ValueError:
            pass


class TestClearWish:
    def test_clears_when_wished_rank_played(self):
        state = _make_state([], active_wish=7)
        clear_wish_if_fulfilled(state, [make_card(7)])
        assert state.active_wish is None

    def test_does_not_clear_for_wrong_rank(self):
        state = _make_state([], active_wish=7)
        clear_wish_if_fulfilled(state, [make_card(8)])
        assert state.active_wish == 7

    def test_does_not_clear_for_phoenix(self):
        state = _make_state([], active_wish=7)
        clear_wish_if_fulfilled(state, [phoenix()])
        assert state.active_wish == 7

    def test_no_wish_active_is_noop(self):
        state = _make_state([])
        clear_wish_if_fulfilled(state, [make_card(7)])
        assert state.active_wish is None

    def test_clears_when_wished_rank_in_multi_card_play(self):
        state = _make_state([], active_wish=5)
        clear_wish_if_fulfilled(state, [make_card(5, "jade"), make_card(5, "sword")])
        assert state.active_wish is None


class TestCheckWishObligation:
    def test_no_wish_active(self):
        state = _make_state([make_card(7)])
        assert not check_wish_obligation(state, 0)

    def test_player_has_wished_card_leading(self):
        state = _make_state([make_card(7), make_card(3)], active_wish=7)
        assert check_wish_obligation(state, 0)

    def test_player_does_not_have_wished_card(self):
        state = _make_state([make_card(8), make_card(3)], active_wish=7)
        assert not check_wish_obligation(state, 0)

    def test_player_has_wished_card_matching_trick_type(self):
        trick = detect_combination([make_card(5)])
        state = _make_state(
            [make_card(7), make_card(3)],
            active_wish=7,
            trick_combo=trick,
        )
        assert check_wish_obligation(state, 0)

    def test_player_has_wished_card_cannot_beat_trick(self):
        trick = detect_combination([make_card(10)])
        state = _make_state(
            [make_card(7), make_card(3)],
            active_wish=7,
            trick_combo=trick,
        )
        assert not check_wish_obligation(state, 0)

    def test_wished_card_in_pair_can_beat_pair(self):
        trick = detect_combination([make_card(5, "jade"), make_card(5, "sword")])
        hand = [make_card(7, "jade"), make_card(7, "sword"), make_card(3)]
        state = _make_state(hand, active_wish=7, trick_combo=trick)
        assert check_wish_obligation(state, 0)

    def test_wished_card_single_rank_not_enough_for_pair(self):
        trick = detect_combination([make_card(5, "jade"), make_card(5, "sword")])
        hand = [make_card(7, "jade"), make_card(3)]
        state = _make_state(hand, active_wish=7, trick_combo=trick)
        assert not check_wish_obligation(state, 0)

    def test_phoenix_does_not_satisfy_wish(self):
        state = _make_state([phoenix(), make_card(3)], active_wish=7)
        assert not check_wish_obligation(state, 0)
