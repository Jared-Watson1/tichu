from __future__ import annotations

from game.models import GameState


def score_round(state: GameState) -> tuple[int, int]:
    """Calculate round point scores for each team. Returns (team0, team1).

    Double victory (teammates 1st and 2nd out) returns 200 flat for that team.
    Otherwise the tailender gives hand cards to opponents and tricks to 1st-out player.
    """
    if _is_double_victory(state, team=0):
        return (200, 0)
    if _is_double_victory(state, team=1):
        return (0, 200)

    first_out_seat = state.out_order[0]
    tailender = _find_tailender(state)

    tailender_hand_points = sum(c.point_value for c in tailender.hand)
    tailender_team = tailender.team
    opponent_team = 1 - tailender_team

    team_points = [0, 0]
    team_points[opponent_team] += tailender_hand_points

    tailender_trick_cards = []
    for trick in tailender.tricks_won:
        tailender_trick_cards.extend(trick)
    tailender_trick_points = sum(c.point_value for c in tailender_trick_cards)

    first_out_player = state.players[first_out_seat]
    first_out_player.tricks_won.append(tailender_trick_cards)
    team_points[first_out_player.team] += tailender_trick_points

    for player in state.players:
        if player.seat == tailender.seat:
            continue
        for trick in player.tricks_won:
            points = sum(c.point_value for c in trick)
            team_points[player.team] += points

    return (team_points[0], team_points[1])


def apply_tichu_bonuses(
    state: GameState, round_scores: tuple[int, int]
) -> tuple[int, int]:
    """Add tichu bonuses/penalties to round scores."""
    scores = list(round_scores)

    first_out_seat = state.out_order[0] if state.out_order else None

    for player in state.players:
        if player.called_tichu is None:
            continue

        if player.called_tichu == "small":
            bonus = 100
        else:
            bonus = 200
        if player.seat == first_out_seat:
            scores[player.team] += bonus
        else:
            scores[player.team] -= bonus

    return (scores[0], scores[1])


def check_game_over(scores: list[int]) -> int | None:
    """Return winning team index if a team reached 1000+. None if game continues.

    If both teams >= 1000, the higher score wins. If tied, no winner yet.
    """
    t0_over = scores[0] >= 1000
    t1_over = scores[1] >= 1000

    if not t0_over and not t1_over:
        return None

    if t0_over and not t1_over:
        return 0
    if t1_over and not t0_over:
        return 1

    if scores[0] > scores[1]:
        return 0
    if scores[1] > scores[0]:
        return 1

    return None


def _is_double_victory(state: GameState, team: int) -> bool:
    if len(state.out_order) < 2:
        return False
    first = state.players[state.out_order[0]]
    second = state.players[state.out_order[1]]
    return first.team == team and second.team == team


def _find_tailender(state: GameState):
    """Find the player who did not go out (or went out last)."""
    for player in state.players:
        if not player.has_gone_out:
            return player
    return state.players[state.out_order[-1]]
