import pytest

from game.engine import EngineError, TichuEngine
from game.models import (
    Card,
    CombinationType,
    GamePhase,
    GameState,
    Player,
    SpecialType,
    Suit,
)
from tests.conftest import dragon, hound, mah_jong, make_card, phoenix


PLAYERS_INFO = [
    {"id": "p0", "name": "Alice"},
    {"id": "p1", "name": "Bob"},
    {"id": "p2", "name": "Charlie"},
    {"id": "p3", "name": "Diana"},
]


def _setup_playing_state(hands: list[list[Card]]) -> GameState:
    """Create a game state in PLAYING phase with specific hands.

    Seats 0,2 = team 0; seats 1,3 = team 1.
    First player in hands[0] is assumed to have turn.
    """
    state = TichuEngine.create_game("test", PLAYERS_INFO)
    state.phase = GamePhase.PLAYING
    for i, hand in enumerate(hands):
        state.players[i].hand = list(hand)
        state.players[i].has_played_card = False
        state.players[i].tricks_won = []
    state.current_player_seat = 0
    state.leading_player_seat = 0
    return state


class TestGameCreation:
    def test_create_game(self):
        state = TichuEngine.create_game("room1", PLAYERS_INFO)
        assert state.phase == GamePhase.WAITING
        assert len(state.players) == 4
        assert state.players[0].team == 0
        assert state.players[1].team == 1
        assert state.players[2].team == 0
        assert state.players[3].team == 1

    def test_create_game_wrong_player_count(self):
        with pytest.raises(EngineError):
            TichuEngine.create_game("room1", PLAYERS_INFO[:3])


class TestRoundStart:
    def test_start_round_deals_8_cards(self):
        state = TichuEngine.create_game("room1", PLAYERS_INFO)
        TichuEngine.start_round(state)
        assert state.phase == GamePhase.GRAND_TICHU
        for player in state.players:
            assert len(player.hand) == 8

    def test_cannot_start_round_in_playing_phase(self):
        state = TichuEngine.create_game("room1", PLAYERS_INFO)
        state.phase = GamePhase.PLAYING
        with pytest.raises(EngineError):
            TichuEngine.start_round(state)


class TestGrandTichu:
    def test_all_decline_transitions_to_pushing(self):
        state = TichuEngine.create_game("room1", PLAYERS_INFO)
        TichuEngine.start_round(state)
        for seat in range(4):
            TichuEngine.grand_tichu_decision(state, seat, False)
        assert state.phase == GamePhase.PUSHING
        for player in state.players:
            assert len(player.hand) == 14

    def test_grand_tichu_call_recorded(self):
        state = TichuEngine.create_game("room1", PLAYERS_INFO)
        TichuEngine.start_round(state)
        TichuEngine.grand_tichu_decision(state, 0, True)
        assert state.players[0].called_tichu == "grand"
        for seat in range(1, 4):
            TichuEngine.grand_tichu_decision(state, seat, False)
        assert state.players[0].called_tichu == "grand"

    def test_cannot_decide_twice(self):
        state = TichuEngine.create_game("room1", PLAYERS_INFO)
        TichuEngine.start_round(state)
        TichuEngine.grand_tichu_decision(state, 0, False)
        with pytest.raises(EngineError):
            TichuEngine.grand_tichu_decision(state, 0, True)


class TestPushCards:
    def _setup_push_state(self) -> GameState:
        state = TichuEngine.create_game("room1", PLAYERS_INFO)
        TichuEngine.start_round(state)
        for seat in range(4):
            TichuEngine.grand_tichu_decision(state, seat, False)
        return state

    def test_push_and_transition_to_playing(self):
        state = self._setup_push_state()
        for seat in range(4):
            hand = state.players[seat].hand
            targets = [s for s in range(4) if s != seat]
            cards_map = {targets[i]: hand[i] for i in range(3)}
            TichuEngine.push_cards(state, seat, cards_map)
        assert state.phase == GamePhase.PLAYING
        for player in state.players:
            assert len(player.hand) == 14

    def test_cannot_push_to_self(self):
        state = self._setup_push_state()
        hand = state.players[0].hand
        with pytest.raises(EngineError):
            TichuEngine.push_cards(state, 0, {0: hand[0], 1: hand[1], 2: hand[2]})

    def test_cannot_push_twice(self):
        state = self._setup_push_state()
        hand = state.players[0].hand
        cards_map = {1: hand[0], 2: hand[1], 3: hand[2]}
        TichuEngine.push_cards(state, 0, cards_map)
        with pytest.raises(EngineError):
            TichuEngine.push_cards(state, 0, {1: hand[3], 2: hand[4], 3: hand[5]})


class TestPlayCards:
    def test_play_single(self):
        hands = [
            [mah_jong(), make_card(5)],
            [make_card(8)],
            [make_card(10)],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        result = TichuEngine.play_cards(state, 0, [mah_jong()])
        assert result["action"] == "play"
        assert len(state.trick) == 1
        assert state.current_player_seat == 1

    def test_cannot_play_out_of_turn(self):
        hands = [
            [make_card(5)],
            [make_card(8)],
            [make_card(10)],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        with pytest.raises(EngineError, match="Not your turn"):
            TichuEngine.play_cards(state, 1, [make_card(8)])

    def test_play_must_beat_trick(self):
        hands = [
            [make_card(10)],
            [make_card(5)],
            [make_card(12)],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        TichuEngine.play_cards(state, 0, [make_card(10)])
        with pytest.raises(EngineError, match="does not beat"):
            TichuEngine.play_cards(state, 1, [make_card(5)])

    def test_player_goes_out(self):
        hands = [
            [make_card(14)],
            [make_card(5)],
            [make_card(10)],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        result = TichuEngine.play_cards(state, 0, [make_card(14)])
        assert result.get("went_out") is True
        assert state.players[0].has_gone_out
        assert state.out_order == [0]

    def test_invalid_combination_rejected(self):
        hands = [
            [make_card(5), make_card(8)],
            [make_card(10)],
            [make_card(12)],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        with pytest.raises(EngineError, match="Invalid combination"):
            TichuEngine.play_cards(state, 0, [make_card(5), make_card(8)])


class TestPassTurn:
    def test_pass_advances_turn(self):
        hands = [
            [make_card(10)],
            [make_card(5)],
            [make_card(12)],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        TichuEngine.play_cards(state, 0, [make_card(10)])
        TichuEngine.pass_turn(state, 1)
        assert state.current_player_seat == 2

    def test_three_passes_wins_trick(self):
        hands = [
            [make_card(14), make_card(3)],
            [make_card(5)],
            [make_card(7)],
            [make_card(2)],
        ]
        state = _setup_playing_state(hands)
        TichuEngine.play_cards(state, 0, [make_card(14)])
        TichuEngine.pass_turn(state, 1)
        TichuEngine.pass_turn(state, 2)
        result = TichuEngine.pass_turn(state, 3)
        assert result.get("trick_won") == 0
        assert len(state.players[0].tricks_won) == 1
        assert state.current_player_seat == 0

    def test_cannot_pass_on_empty_trick(self):
        state = _setup_playing_state([
            [make_card(5)], [make_card(8)], [make_card(10)], [make_card(3)],
        ])
        with pytest.raises(EngineError, match="Cannot pass on empty"):
            TichuEngine.pass_turn(state, 0)

    def test_cannot_pass_out_of_turn(self):
        state = _setup_playing_state([
            [make_card(5)], [make_card(8)], [make_card(10)], [make_card(3)],
        ])
        TichuEngine.play_cards(state, 0, [make_card(5)])
        with pytest.raises(EngineError, match="Not your turn"):
            TichuEngine.pass_turn(state, 2)


class TestBombInterrupt:
    def test_bomb_out_of_turn(self):
        hands = [
            [make_card(5)],
            [make_card(7)],
            [make_card(9, "jade"), make_card(9, "sword"),
             make_card(9, "pagoda"), make_card(9, "star")],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        TichuEngine.play_cards(state, 0, [make_card(5)])
        assert state.current_player_seat == 1

        result = TichuEngine.play_cards(state, 2, [
            make_card(9, "jade"), make_card(9, "sword"),
            make_card(9, "pagoda"), make_card(9, "star"),
        ])
        assert result["action"] == "play"
        assert result.get("went_out") is True


class TestHoundLead:
    def test_hound_transfers_to_partner(self):
        hands = [
            [hound(), make_card(5)],
            [make_card(8)],
            [make_card(10)],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        result = TichuEngine.play_cards(state, 0, [hound()])
        assert result["action"] == "hound_lead"
        assert result["transfer_to"] == 2
        assert state.current_player_seat == 2

    def test_hound_partner_out_transfers_to_next(self):
        hands = [
            [hound(), make_card(5)],
            [make_card(8)],
            [],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        state.players[2].has_gone_out = True
        state.out_order = [2]
        result = TichuEngine.play_cards(state, 0, [hound()])
        assert result["transfer_to"] == 3


class TestDragonGive:
    def test_dragon_trick_prompts_give(self):
        hands = [
            [dragon(), make_card(5)],
            [make_card(8)],
            [make_card(10)],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        TichuEngine.play_cards(state, 0, [dragon()])
        TichuEngine.pass_turn(state, 1)
        TichuEngine.pass_turn(state, 2)
        result = TichuEngine.pass_turn(state, 3)
        assert result.get("needs_dragon_give") is True
        assert state.pending_dragon_give is True

    def test_dragon_give_to_opponent(self):
        hands = [
            [dragon(), make_card(5)],
            [make_card(8)],
            [make_card(10)],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        TichuEngine.play_cards(state, 0, [dragon()])
        TichuEngine.pass_turn(state, 1)
        TichuEngine.pass_turn(state, 2)
        TichuEngine.pass_turn(state, 3)

        result = TichuEngine.dragon_give(state, 0, 1)
        assert result["action"] == "dragon_give"
        assert result["recipient"] == 1
        assert len(state.players[1].tricks_won) == 1
        assert any(
            c.special == SpecialType.DRAGON
            for c in state.players[1].tricks_won[0]
        )

    def test_dragon_give_must_be_opponent(self):
        hands = [
            [dragon(), make_card(5)],
            [make_card(8)],
            [make_card(10)],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        TichuEngine.play_cards(state, 0, [dragon()])
        TichuEngine.pass_turn(state, 1)
        TichuEngine.pass_turn(state, 2)
        TichuEngine.pass_turn(state, 3)

        with pytest.raises(EngineError, match="opponent"):
            TichuEngine.dragon_give(state, 0, 2)

    def test_cannot_play_during_pending_dragon(self):
        hands = [
            [dragon(), make_card(5)],
            [make_card(8)],
            [make_card(10)],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        TichuEngine.play_cards(state, 0, [dragon()])
        TichuEngine.pass_turn(state, 1)
        TichuEngine.pass_turn(state, 2)
        TichuEngine.pass_turn(state, 3)

        with pytest.raises(EngineError, match="dragon give"):
            TichuEngine.play_cards(state, 0, [make_card(5)])


class TestSmallTichu:
    def test_call_small_tichu(self):
        state = _setup_playing_state([
            [make_card(5)], [make_card(8)], [make_card(10)], [make_card(3)],
        ])
        TichuEngine.call_small_tichu(state, 0)
        assert state.players[0].called_tichu == "small"

    def test_cannot_call_after_playing(self):
        state = _setup_playing_state([
            [make_card(5), make_card(8)],
            [make_card(10)], [make_card(12)], [make_card(3)],
        ])
        TichuEngine.play_cards(state, 0, [make_card(5)])
        with pytest.raises(EngineError, match="after playing"):
            TichuEngine.call_small_tichu(state, 0)

    def test_cannot_call_twice(self):
        state = _setup_playing_state([
            [make_card(5)], [make_card(8)], [make_card(10)], [make_card(3)],
        ])
        TichuEngine.call_small_tichu(state, 0)
        with pytest.raises(EngineError, match="Already called"):
            TichuEngine.call_small_tichu(state, 0)


class TestWishEnforcement:
    def test_must_play_wished_rank(self):
        hands = [
            [mah_jong(), make_card(5)],
            [make_card(7), make_card(3)],
            [make_card(10)],
            [make_card(2)],
        ]
        state = _setup_playing_state(hands)
        TichuEngine.play_cards(state, 0, [mah_jong()])
        TichuEngine.make_wish(state, 0, 7)

        with pytest.raises(EngineError, match="wished rank"):
            TichuEngine.play_cards(state, 1, [make_card(3)])

    def test_wish_fulfilled_clears(self):
        hands = [
            [mah_jong(), make_card(5)],
            [make_card(7), make_card(3)],
            [make_card(10)],
            [make_card(2)],
        ]
        state = _setup_playing_state(hands)
        TichuEngine.play_cards(state, 0, [mah_jong()])
        TichuEngine.make_wish(state, 0, 7)
        TichuEngine.play_cards(state, 1, [make_card(7)])
        assert state.active_wish is None

    def test_skip_wish_allowed(self):
        hands = [
            [mah_jong(), make_card(5)],
            [make_card(7)],
            [make_card(10)],
            [make_card(2)],
        ]
        state = _setup_playing_state(hands)
        TichuEngine.play_cards(state, 0, [mah_jong()])
        TichuEngine.skip_wish(state, 0)
        assert state.active_wish is None
        assert state.pending_wish_from_seat is None


class TestTurnManagement:
    def test_skips_out_players(self):
        hands = [
            [make_card(14), make_card(5)],
            [],
            [make_card(10)],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        state.players[1].has_gone_out = True
        state.out_order = [1]
        TichuEngine.play_cards(state, 0, [make_card(14)])
        assert state.current_player_seat == 2

    def test_trick_winner_out_next_player_leads(self):
        hands = [
            [make_card(14)],
            [make_card(5)],
            [make_card(10)],
            [make_card(3)],
        ]
        state = _setup_playing_state(hands)
        TichuEngine.play_cards(state, 0, [make_card(14)])
        # seat 0 went out, 3 active players remain so 2 passes win the trick
        TichuEngine.pass_turn(state, 1)
        result = TichuEngine.pass_turn(state, 2)
        assert result.get("trick_won") == 0
        assert state.current_player_seat == 1


class TestRoundEnd:
    def test_round_ends_when_three_out(self):
        hands = [
            [make_card(14)],
            [make_card(13)],
            [make_card(12)],
            [make_card(3), make_card(2)],
        ]
        state = _setup_playing_state(hands)
        # seat 0 plays and goes out (3 active remain, 2 passes win trick)
        TichuEngine.play_cards(state, 0, [make_card(14)])
        TichuEngine.pass_turn(state, 1)
        TichuEngine.pass_turn(state, 2)
        # trick won by seat 0 (out), seat 1 leads. seat 1 goes out (2 active, 1 pass wins)
        TichuEngine.play_cards(state, 1, [make_card(13)])
        TichuEngine.pass_turn(state, 2)
        # trick won by seat 1 (out), seat 2 leads. seat 2 goes out, round ends
        result = TichuEngine.play_cards(state, 2, [make_card(12)])
        assert result.get("round_over") is True
        assert state.phase in (GamePhase.ROUND_OVER, GamePhase.GAME_OVER)


class TestDoubleVictoryIntegration:
    def test_double_victory_scores_200(self):
        hands = [
            [make_card(14)],
            [make_card(5), make_card(4)],
            [make_card(13)],
            [make_card(3), make_card(2)],
        ]
        state = _setup_playing_state(hands)
        # seat 0 (team 0) plays ace and goes out
        TichuEngine.play_cards(state, 0, [make_card(14)])
        # 3 active remain, 2 passes win trick
        TichuEngine.pass_turn(state, 1)
        TichuEngine.pass_turn(state, 2)
        # trick won by seat 0 (out), seat 1 leads
        TichuEngine.play_cards(state, 1, [make_card(5)])
        # seat 2 (team 0) beats with king and goes out -> double victory (seats 0,2 both team 0)
        result = TichuEngine.play_cards(state, 2, [make_card(13)])
        assert result.get("went_out") is True
        assert result.get("round_over") is True
        assert state.scores[0] == 200
        assert state.scores[1] == 0


class TestDragonGiveIntegration:
    def test_dragon_points_go_to_chosen_opponent(self):
        hands = [
            [dragon()],
            [make_card(5), make_card(3)],
            [make_card(10)],
            [make_card(2)],
        ]
        state = _setup_playing_state(hands)
        TichuEngine.play_cards(state, 0, [dragon()])
        # seat 0 went out, 3 active remain, 2 passes win trick
        TichuEngine.pass_turn(state, 1)
        result = TichuEngine.pass_turn(state, 2)
        assert result.get("needs_dragon_give") is True

        TichuEngine.dragon_give(state, 0, 1)
        assert any(
            c.special == SpecialType.DRAGON
            for trick in state.players[1].tricks_won
            for c in trick
        )


class TestBombInterruptIntegration:
    def test_bomb_beats_high_single(self):
        hands = [
            [make_card(14), make_card(3)],
            [make_card(5)],
            [make_card(9, "jade"), make_card(9, "sword"),
             make_card(9, "pagoda"), make_card(9, "star"), make_card(2)],
            [make_card(7)],
        ]
        state = _setup_playing_state(hands)
        TichuEngine.play_cards(state, 0, [make_card(14)])

        TichuEngine.play_cards(state, 2, [
            make_card(9, "jade"), make_card(9, "sword"),
            make_card(9, "pagoda"), make_card(9, "star"),
        ])

        TichuEngine.pass_turn(state, 3)
        TichuEngine.pass_turn(state, 0)
        result = TichuEngine.pass_turn(state, 1)
        assert result.get("trick_won") == 2
        assert len(state.players[2].tricks_won) == 1


class TestFullHandSimulation:
    def test_complete_hand(self):
        """Simulate a complete hand from start to round end."""
        state = TichuEngine.create_game("test", PLAYERS_INFO)
        TichuEngine.start_round(state)

        for seat in range(4):
            TichuEngine.grand_tichu_decision(state, seat, False)
        assert state.phase == GamePhase.PUSHING

        for seat in range(4):
            hand = state.players[seat].hand
            targets = [s for s in range(4) if s != seat]
            cards_map = {targets[i]: hand[i] for i in range(3)}
            TichuEngine.push_cards(state, seat, cards_map)
        assert state.phase == GamePhase.PLAYING

        for player in state.players:
            assert len(player.hand) == 14

        mah_jong_seat = state.current_player_seat
        has_mah_jong = any(
            c.special == SpecialType.MAH_JONG
            for c in state.players[mah_jong_seat].hand
        )
        assert has_mah_jong
