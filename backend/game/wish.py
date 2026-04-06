from __future__ import annotations

from itertools import combinations as iter_combinations

from game.combinations import can_play_on, detect_combination
from game.models import Card, Combination, GameState, SpecialType


def set_wish(state: GameState, rank: int) -> None:
    if rank < 2 or rank > 14:
        raise ValueError("Wish rank must be between 2 and 14")
    state.active_wish = rank
    state.pending_wish_from_seat = None


def clear_wish_if_fulfilled(state: GameState, played_cards: list[Card]) -> None:
    if state.active_wish is None:
        return
    for card in played_cards:
        if card.special is None and card.rank == state.active_wish:
            state.active_wish = None
            return


def check_wish_obligation(state: GameState, player_seat: int) -> bool:
    """Return True if the player holds the wished rank and can legally play it."""
    if state.active_wish is None:
        return False

    player = state.players[player_seat]
    wished_cards = [
        c for c in player.hand
        if c.special is None and c.rank == state.active_wish
    ]
    if not wished_cards:
        return False

    current_trick_combo = _current_trick_top(state)
    if current_trick_combo is None:
        return True

    return _can_use_wished_card_in_combination(
        player.hand, state.active_wish, current_trick_combo
    )


def get_wish_valid_plays(state: GameState, player_seat: int) -> list[list[Card]]:
    """Return all valid plays that include the wished rank card."""
    if state.active_wish is None:
        return []

    player = state.players[player_seat]
    wished_cards = [
        c for c in player.hand
        if c.special is None and c.rank == state.active_wish
    ]
    if not wished_cards:
        return []

    current_trick_combo = _current_trick_top(state)
    valid_plays: list[list[Card]] = []

    for wished_card in wished_cards:
        if current_trick_combo is None:
            valid_plays.append([wished_card])
            continue

        for size in range(1, len(player.hand) + 1):
            for card_set in iter_combinations(player.hand, size):
                cards = list(card_set)
                if wished_card not in cards:
                    continue
                combo = detect_combination(cards)
                if combo is not None and can_play_on(combo, current_trick_combo):
                    valid_plays.append(cards)

    return valid_plays


def _current_trick_top(state: GameState) -> Combination | None:
    if not state.trick:
        return None
    return state.trick[-1][1]


def _can_use_wished_card_in_combination(
    hand: list[Card],
    wished_rank: int,
    current_trick: Combination,
) -> bool:
    wished_cards = [
        c for c in hand if c.special is None and c.rank == wished_rank
    ]
    if not wished_cards:
        return False

    for size in range(1, len(hand) + 1):
        for card_set in iter_combinations(hand, size):
            cards = list(card_set)
            has_wished = any(
                c.special is None and c.rank == wished_rank for c in cards
            )
            if not has_wished:
                continue
            combo = detect_combination(cards)
            if combo is not None and can_play_on(combo, current_trick):
                return True

    return False
