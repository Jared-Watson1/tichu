from __future__ import annotations

import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

from ai.player import ai_decide
from game.engine import EngineError, TichuEngine
from game.models import Card, GamePhase, GameState
from lobby.manager import LobbyManager
from lobby.models import LobbyError
from ws.broadcaster import (
    broadcast_game_state,
    send_event,
    send_to_player,
    _get_valid_actions,
)
from ws.protocol import (
    ClientMsgType,
    ProtocolError,
    ServerMsgType,
    parse_cards_from_payload,
    parse_client_message,
)

logger = logging.getLogger(__name__)


async def websocket_handler(websocket: WebSocket, lobby: LobbyManager) -> None:
    await websocket.accept()
    player_id: str | None = None
    game_id: str | None = None

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                msg_type, payload = parse_client_message(raw)
            except ProtocolError as exc:
                await send_to_player(
                    websocket, ServerMsgType.ERROR,
                    {"message": str(exc), "code": "protocol_error"},
                )
                continue

            try:
                if msg_type == ClientMsgType.CREATE_GAME:
                    game_id, player_id = lobby.create_game(
                        payload.get("player_name", "Player"), websocket
                    )
                    await send_to_player(
                        websocket, ServerMsgType.GAME_CREATED,
                        {"game_id": game_id, "player_id": player_id, "seat": 0},
                    )

                elif msg_type == ClientMsgType.JOIN_GAME:
                    join_game_id = payload.get("game_id", "")
                    reconnect_id = payload.get("player_id")

                    if reconnect_id:
                        seat = lobby.reconnect(join_game_id, reconnect_id, websocket)
                        player_id = reconnect_id
                        game_id = join_game_id

                        await send_event(
                            lobby, game_id, ServerMsgType.PLAYER_RECONNECTED,
                            {"seat": seat, "player_name": payload.get("player_name", "")},
                        )

                        room = lobby.get_room(game_id)
                        if room and room.game_state:
                            await broadcast_game_state(lobby, game_id, room.game_state)
                    else:
                        player_id, seat = lobby.join_game(
                            join_game_id, payload.get("player_name", "Player"), websocket
                        )
                        game_id = join_game_id
                        room = lobby.get_room(game_id)
                        player_names = {
                            s: c.player_name for s, c in room.players.items()
                        } if room else {}

                        await send_to_player(
                            websocket, ServerMsgType.PLAYER_JOINED,
                            {
                                "player_id": player_id,
                                "seat": seat,
                                "team": seat % 2,
                            },
                        )
                        await send_event(
                            lobby, game_id, ServerMsgType.PLAYER_JOINED,
                            {
                                "player_name": payload.get("player_name", "Player"),
                                "seat": seat,
                                "team": seat % 2,
                                "players": player_names,
                            },
                        )

                elif msg_type == ClientMsgType.ADD_AI_PLAYER:
                    if game_id is None:
                        raise LobbyError("Not in a game room")
                    ai_player_id, ai_seat = lobby.add_ai_player(game_id)
                    room = lobby.get_room(game_id)
                    ai_name = room.players[ai_seat].player_name if room else "Claude"
                    player_names = {
                        s: c.player_name for s, c in room.players.items()
                    } if room else {}
                    await send_event(
                        lobby, game_id, ServerMsgType.PLAYER_JOINED,
                        {
                            "player_name": ai_name,
                            "seat": ai_seat,
                            "team": ai_seat % 2,
                            "players": player_names,
                        },
                    )

                elif msg_type == ClientMsgType.START_GAME:
                    if game_id is None:
                        raise LobbyError("Not in a game room")

                    room = lobby.get_room(game_id)
                    if room and room.game_state and room.game_state.phase == GamePhase.ROUND_OVER:
                        TichuEngine.start_round(room.game_state)
                        await send_event(
                            lobby, game_id, ServerMsgType.GAME_STARTING, {}
                        )
                        await broadcast_game_state(lobby, game_id, room.game_state)
                        await _maybe_trigger_ai(lobby, game_id, room.game_state)
                    else:
                        state = lobby.start_game(game_id)
                        await send_event(
                            lobby, game_id, ServerMsgType.GAME_STARTING, {}
                        )
                        await broadcast_game_state(lobby, game_id, state)
                        await _maybe_trigger_ai(lobby, game_id, state)

                else:
                    await _handle_game_message(
                        websocket, lobby, player_id, game_id, msg_type, payload
                    )

            except (EngineError, LobbyError) as exc:
                await send_to_player(
                    websocket, ServerMsgType.ERROR,
                    {
                        "message": str(exc),
                        "code": "engine_error" if isinstance(exc, EngineError) else "lobby_error",
                    },
                )

    except WebSocketDisconnect:
        pass
    finally:
        if player_id:
            disconnected_game_id = lobby.handle_disconnect(player_id)
            if disconnected_game_id:
                room = lobby.get_room(disconnected_game_id)
                seat = None
                if room:
                    for s, dc in room.disconnected_players.items():
                        if dc.player_id == player_id:
                            seat = s
                            break
                if seat is not None:
                    await send_event(
                        lobby, disconnected_game_id, ServerMsgType.PLAYER_DISCONNECTED,
                        {"seat": seat},
                    )


async def _handle_game_message(
    websocket: WebSocket,
    lobby: LobbyManager,
    player_id: str | None,
    game_id: str | None,
    msg_type: ClientMsgType,
    payload: dict,
) -> None:
    if player_id is None or game_id is None:
        raise LobbyError("Not in a game")

    result = lobby.get_player_room_and_seat(player_id)
    if result is None:
        raise LobbyError("Player not found in any room")

    room, seat = result
    state = room.game_state
    if state is None:
        raise LobbyError("Game has not started")

    if msg_type == ClientMsgType.GRAND_TICHU_DECISION:
        TichuEngine.grand_tichu_decision(state, seat, payload.get("call", False))
        if payload.get("call"):
            await send_event(
                lobby, game_id, ServerMsgType.TICHU_CALLED,
                {"seat": seat, "tichu_type": "grand"},
            )

    elif msg_type == ClientMsgType.PUSH_CARDS:
        raw_map = payload.get("cards", {})
        cards_map: dict[int, Card] = {}
        for target_seat_str, card_data in raw_map.items():
            cards_map[int(target_seat_str)] = Card(**card_data)
        TichuEngine.push_cards(state, seat, cards_map)

    elif msg_type in (ClientMsgType.PLAY_CARDS, ClientMsgType.PLAY_BOMB):
        cards = parse_cards_from_payload(payload)
        action_result = TichuEngine.play_cards(state, seat, cards)
        await _process_action_result(lobby, game_id, state, action_result)

    elif msg_type == ClientMsgType.PASS_TURN:
        action_result = TichuEngine.pass_turn(state, seat)
        await _process_action_result(lobby, game_id, state, action_result)

    elif msg_type == ClientMsgType.CALL_SMALL_TICHU:
        TichuEngine.call_small_tichu(state, seat)
        await send_event(
            lobby, game_id, ServerMsgType.TICHU_CALLED,
            {"seat": seat, "tichu_type": "small"},
        )

    elif msg_type == ClientMsgType.MAKE_WISH:
        rank = payload.get("rank")
        TichuEngine.make_wish(state, seat, rank)
        await send_event(
            lobby, game_id, ServerMsgType.WISH_MADE, {"rank": rank}
        )

    elif msg_type == ClientMsgType.SKIP_WISH:
        TichuEngine.skip_wish(state, seat)

    elif msg_type == ClientMsgType.DRAGON_GIVE:
        opponent_seat = payload.get("opponent_seat")
        action_result = TichuEngine.dragon_give(state, seat, opponent_seat)
        await _process_action_result(lobby, game_id, state, action_result)

    await broadcast_game_state(lobby, game_id, state)
    await _maybe_trigger_ai(lobby, game_id, state)


async def _process_action_result(
    lobby: LobbyManager, game_id: str, state: GameState, result: dict
) -> None:
    if result.get("combination"):
        combo = result["combination"]
        await send_event(
            lobby, game_id, ServerMsgType.CARDS_PLAYED,
            {"seat": result["seat"], "combination": combo.model_dump()},
        )

    if result.get("action") == "pass":
        await send_event(
            lobby, game_id, ServerMsgType.PLAYER_PASSED,
            {"seat": result["seat"]},
        )

    if result.get("went_out"):
        player = state.players[result["seat"]]
        await send_event(
            lobby, game_id, ServerMsgType.PLAYER_OUT,
            {"seat": result["seat"], "position": player.out_order},
        )

    if result.get("trick_won") is not None:
        await send_event(
            lobby, game_id, ServerMsgType.TRICK_WON,
            {"seat": result["trick_won"]},
        )

    if result.get("round_over"):
        await send_event(
            lobby, game_id, ServerMsgType.ROUND_OVER,
            {
                "scores": state.scores,
                "round_number": state.round_number,
            },
        )
        if state.phase == GamePhase.GAME_OVER:
            winning_team = 0 if state.scores[0] > state.scores[1] else 1
            await send_event(
                lobby, game_id, ServerMsgType.GAME_OVER,
                {"winning_team": winning_team, "final_scores": state.scores},
            )


AI_MOVE_DELAY = 0.5
MAX_AI_CONSECUTIVE = 20


async def _maybe_trigger_ai(
    lobby: LobbyManager, game_id: str, state: GameState
) -> None:
    """Check if any AI player needs to act and trigger decisions in a loop."""
    if state.phase in (GamePhase.WAITING, GamePhase.GAME_OVER):
        return

    room = lobby.get_room(game_id)
    if room is None or not room.ai_seats:
        return

    for _ in range(MAX_AI_CONSECUTIVE):
        ai_seat = _find_ai_seat_needing_action(room.ai_seats, state)
        if ai_seat is None:
            break

        await asyncio.sleep(AI_MOVE_DELAY)

        try:
            action_result = await ai_decide(state, ai_seat)
        except Exception:
            logger.exception("AI decide failed for seat %d", ai_seat)
            break

        if action_result is not None:
            await _process_action_result(lobby, game_id, state, action_result)

        await broadcast_game_state(lobby, game_id, state)

        if state.phase in (GamePhase.GAME_OVER, GamePhase.ROUND_OVER, GamePhase.WAITING):
            break


def _find_ai_seat_needing_action(ai_seats: set[int], state: GameState) -> int | None:
    for seat in sorted(ai_seats):
        actions = _get_valid_actions(state, seat)
        if actions:
            return seat
    return None
