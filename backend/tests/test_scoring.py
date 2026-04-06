from game.models import Card, GamePhase, GameState, Player, Suit, SpecialType
from game.scoring import apply_tichu_bonuses, check_game_over, score_round
from tests.conftest import dragon, make_card, phoenix


def _make_player(seat: int, **kwargs) -> Player:
    return Player(
        id=f"p{seat}",
        name=f"Player {seat}",
        team=seat % 2,
        seat=seat,
        **kwargs,
    )


def _make_state(**kwargs) -> GameState:
    players = kwargs.pop("players", [_make_player(i) for i in range(4)])
    return GameState(
        id="test",
        phase=GamePhase.ROUND_OVER,
        players=players,
        **kwargs,
    )


class TestDoubleVictory:
    def test_team_0_double_victory(self):
        state = _make_state(out_order=[0, 2, 1, 3])
        state.players[0].has_gone_out = True
        state.players[0].out_order = 1
        state.players[2].has_gone_out = True
        state.players[2].out_order = 2
        state.players[1].has_gone_out = True
        state.players[1].out_order = 3
        state.players[3].has_gone_out = True
        state.players[3].out_order = 4
        scores = score_round(state)
        assert scores == (200, 0)

    def test_team_1_double_victory(self):
        state = _make_state(out_order=[1, 3, 0, 2])
        state.players[1].has_gone_out = True
        state.players[1].out_order = 1
        state.players[3].has_gone_out = True
        state.players[3].out_order = 2
        state.players[0].has_gone_out = True
        state.players[0].out_order = 3
        state.players[2].has_gone_out = True
        state.players[2].out_order = 4
        scores = score_round(state)
        assert scores == (0, 200)


class TestNormalScoring:
    def test_tailender_cards_go_to_opponents(self):
        state = _make_state(out_order=[0, 1, 2])
        state.players[0].has_gone_out = True
        state.players[0].out_order = 1
        state.players[1].has_gone_out = True
        state.players[1].out_order = 2
        state.players[2].has_gone_out = True
        state.players[2].out_order = 3

        # seat 3 (team 1) is tailender with a king in hand
        state.players[3].hand = [make_card(13, "jade")]
        state.players[3].tricks_won = []

        scores = score_round(state)
        # king (10 pts) goes to opponents of team 1 = team 0
        assert scores[0] >= 10

    def test_tailender_tricks_go_to_first_out(self):
        state = _make_state(out_order=[0, 1, 2])
        state.players[0].has_gone_out = True
        state.players[0].out_order = 1
        state.players[1].has_gone_out = True
        state.players[1].out_order = 2
        state.players[2].has_gone_out = True
        state.players[2].out_order = 3

        state.players[3].hand = []
        state.players[3].tricks_won = [[make_card(10, "jade")]]

        scores = score_round(state)
        # seat 0 (team 0) is first out, gets tailender tricks (10 pts)
        assert scores[0] >= 10

    def test_total_points_sum_to_100(self):
        """All point cards distributed across tricks and tailender hand sum to 100."""
        state = _make_state(out_order=[0, 1, 2])
        state.players[0].has_gone_out = True
        state.players[0].out_order = 1
        state.players[1].has_gone_out = True
        state.players[1].out_order = 2
        state.players[2].has_gone_out = True
        state.players[2].out_order = 3

        # All point cards: dragon(25), phoenix(-25), 4x king(40), 4x ten(40), 4x five(20) = 100
        state.players[0].tricks_won = [
            [dragon(),
             make_card(5, "jade"), make_card(5, "sword"),
             make_card(10, "jade")]
        ]
        state.players[1].tricks_won = [
            [phoenix(),
             make_card(13, "jade"), make_card(13, "sword"),
             make_card(10, "sword")]
        ]
        state.players[2].tricks_won = [
            [make_card(5, "pagoda"), make_card(5, "star"),
             make_card(13, "pagoda")]
        ]
        # tailender (seat 3, team 1)
        state.players[3].hand = [
            make_card(13, "star"),
            make_card(10, "pagoda"), make_card(10, "star"),
        ]
        state.players[3].tricks_won = []

        scores = score_round(state)
        assert scores[0] + scores[1] == 100


class TestTichuBonuses:
    def test_small_tichu_success(self):
        state = _make_state(out_order=[0])
        state.players[0].called_tichu = "small"
        scores = apply_tichu_bonuses(state, (50, 50))
        assert scores == (150, 50)

    def test_small_tichu_failure(self):
        state = _make_state(out_order=[1])
        state.players[0].called_tichu = "small"
        scores = apply_tichu_bonuses(state, (50, 50))
        assert scores == (-50, 50)

    def test_grand_tichu_success(self):
        state = _make_state(out_order=[2])
        state.players[2].called_tichu = "grand"
        scores = apply_tichu_bonuses(state, (50, 50))
        assert scores == (250, 50)

    def test_grand_tichu_failure(self):
        state = _make_state(out_order=[1])
        state.players[2].called_tichu = "grand"
        scores = apply_tichu_bonuses(state, (50, 50))
        assert scores == (-150, 50)

    def test_multiple_tichu_calls(self):
        state = _make_state(out_order=[0])
        state.players[0].called_tichu = "small"
        state.players[1].called_tichu = "grand"
        scores = apply_tichu_bonuses(state, (50, 50))
        # team 0: +100, team 1: -200
        assert scores == (150, -150)


class TestCheckGameOver:
    def test_no_winner(self):
        assert check_game_over([500, 600]) is None

    def test_team_0_wins(self):
        assert check_game_over([1000, 500]) == 0

    def test_team_1_wins(self):
        assert check_game_over([500, 1050]) == 1

    def test_both_over_higher_wins(self):
        assert check_game_over([1100, 1000]) == 0
        assert check_game_over([1000, 1100]) == 1

    def test_tied_at_1000_no_winner(self):
        assert check_game_over([1000, 1000]) is None
