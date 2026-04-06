from __future__ import annotations

import asyncio
from collections import Counter
from typing import TYPE_CHECKING

from game.combinations import can_play_on, detect_combination
from game.models import (
    Card,
    Combination,
    GamePhase,
    GameState,
)
from ws.protocol import ServerMsgType, server_message

if TYPE_CHECKING:
    from lobby.manager import LobbyManager


def create_player_view(state: GameState, player_seat: int) -> dict:
    player = state.players[player_seat]
    return {
        "phase": state.phase.value,
        "your_hand": [card.model_dump() for card in player.hand],
        "your_seat": player_seat,
        "players": [
            {
                "name": p.name,
                "seat": p.seat,
                "team": p.team,
                "card_count": len(p.hand),
                "has_gone_out": p.has_gone_out,
                "called_tichu": p.called_tichu,
            }
            for p in state.players
        ],
        "current_player_seat": state.current_player_seat,
        "trick": [
            {"seat": seat, "combination": combo.model_dump()}
            for seat, combo in state.trick
        ],
        "active_wish": state.active_wish,
        "scores": state.scores,
        "round_number": state.round_number,
        "consecutive_passes": state.consecutive_passes,
        "out_order": state.out_order,
        "can_play": _is_player_turn(state, player_seat),
        "valid_actions": _get_valid_actions(state, player_seat),
    }


def _is_player_turn(state: GameState, seat: int) -> bool:
    if state.phase != GamePhase.PLAYING:
        return False
    if state.players[seat].has_gone_out:
        return False
    if state.current_player_seat == seat:
        return True
    if state.trick and _player_has_playable_bomb(state, seat):
        return True
    return False


def _get_valid_actions(state: GameState, seat: int) -> list[str]:
    player = state.players[seat]

    if state.phase == GamePhase.GRAND_TICHU:
        if seat not in state.grand_tichu_decisions:
            return ["grand_tichu_decision"]
        return []

    if state.phase == GamePhase.PUSHING:
        if not player.has_pushed:
            return ["push_cards"]
        return []

    if state.phase == GamePhase.PLAYING:
        if player.has_gone_out:
            return []

        if state.pending_wish_from_seat == seat:
            return ["make_wish", "skip_wish"]

        if state.pending_dragon_give and state.dragon_player_seat == seat:
            return ["dragon_give"]

        actions: list[str] = []

        if state.current_player_seat == seat:
            actions.append("play_cards")
            if state.trick:
                actions.append("pass")
        elif state.trick and _player_has_playable_bomb(state, seat):
            actions.append("play_bomb")

        if not player.has_played_card and player.called_tichu is None:
            actions.append("call_small_tichu")

        return actions

    if state.phase == GamePhase.ROUND_OVER:
        return ["start_game"]

    return []


def _player_has_playable_bomb(state: GameState, seat: int) -> bool:
    hand = state.players[seat].hand
    if len(hand) < 4:
        return False

    current_trick_top = state.trick[-1][1] if state.trick else None
    bombs = _find_bombs_in_hand(hand)

    for bomb in bombs:
        if can_play_on(bomb, current_trick_top):
            return True
    return False


def _find_bombs_in_hand(hand: list[Card]) -> list[Combination]:
    bombs: list[Combination] = []
    normal_cards = [c for c in hand if not c.is_special]

    rank_counts = Counter(c.rank for c in normal_cards)
    for rank, count in rank_counts.items():
        if count == 4:
            four = [c for c in normal_cards if c.rank == rank]
            bombs.append(Combination(
                type="four_bomb",
                cards=four,
                rank=float(rank),
                length=4,
                is_bomb=True,
            ))

    suit_groups: dict[str, list[int]] = {}
    for c in normal_cards:
        suit_groups.setdefault(c.suit, []).append(c.rank)

    for suit, ranks in suit_groups.items():
        if len(ranks) < 5:
            continue
        sorted_ranks = sorted(set(ranks))
        run_start = 0
        for i in range(1, len(sorted_ranks)):
            if sorted_ranks[i] != sorted_ranks[i - 1] + 1:
                if i - run_start >= 5:
                    run = sorted_ranks[run_start:i]
                    run_cards = [
                        c for c in normal_cards
                        if c.suit == suit and c.rank in set(run)
                    ]
                    bombs.append(Combination(
                        type="straight_bomb",
                        cards=run_cards,
                        rank=float(run[-1]),
                        length=len(run),
                        is_bomb=True,
                    ))
                run_start = i
        remaining = sorted_ranks[run_start:]
        if len(remaining) >= 5:
            run_cards = [
                c for c in normal_cards
                if c.suit == suit and c.rank in set(remaining)
            ]
            bombs.append(Combination(
                type="straight_bomb",
                cards=run_cards,
                rank=float(remaining[-1]),
                length=len(remaining),
                is_bomb=True,
            ))

    return bombs


async def broadcast_game_state(
    lobby: LobbyManager, game_id: str, state: GameState
) -> None:
    connections = lobby.get_all_connected(game_id)
    if not connections:
        return

    async def _send_to_one(seat: int, ws: object) -> None:
        view = create_player_view(state, seat)
        msg = server_message(ServerMsgType.GAME_STATE, view)
        try:
            await ws.send_text(msg)
        except Exception:
            pass

    await asyncio.gather(*[_send_to_one(seat, ws) for seat, ws in connections])


async def send_event(
    lobby: LobbyManager,
    game_id: str,
    msg_type: ServerMsgType,
    payload: dict,
) -> None:
    connections = lobby.get_all_connected(game_id)
    msg = server_message(msg_type, payload)

    async def _send(ws: object) -> None:
        try:
            await ws.send_text(msg)
        except Exception:
            pass

    await asyncio.gather(*[_send(ws) for _, ws in connections])


async def send_to_player(
    websocket: object, msg_type: ServerMsgType, payload: dict
) -> None:
    msg = server_message(msg_type, payload)
    try:
        await websocket.send_text(msg)
    except Exception:
        pass
