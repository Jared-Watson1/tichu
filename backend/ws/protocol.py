from __future__ import annotations

import json
from enum import Enum

from game.models import Card


class ProtocolError(Exception):
    pass


class ClientMsgType(str, Enum):
    CREATE_GAME = "create_game"
    JOIN_GAME = "join_game"
    START_GAME = "start_game"
    GRAND_TICHU_DECISION = "grand_tichu_decision"
    PUSH_CARDS = "push_cards"
    PLAY_CARDS = "play_cards"
    PASS_TURN = "pass_turn"
    CALL_SMALL_TICHU = "call_small_tichu"
    MAKE_WISH = "make_wish"
    SKIP_WISH = "skip_wish"
    DRAGON_GIVE = "dragon_give"
    PLAY_BOMB = "play_bomb"
    ADD_AI_PLAYER = "add_ai_player"


class ServerMsgType(str, Enum):
    GAME_CREATED = "game_created"
    PLAYER_JOINED = "player_joined"
    GAME_STARTING = "game_starting"
    GAME_STATE = "game_state"
    CARDS_PLAYED = "cards_played"
    PLAYER_PASSED = "player_passed"
    TRICK_WON = "trick_won"
    TICHU_CALLED = "tichu_called"
    WISH_MADE = "wish_made"
    WISH_FULFILLED = "wish_fulfilled"
    PLAYER_OUT = "player_out"
    ROUND_OVER = "round_over"
    GAME_OVER = "game_over"
    ERROR = "error"
    PLAYER_DISCONNECTED = "player_disconnected"
    PLAYER_RECONNECTED = "player_reconnected"


_CLIENT_MSG_LOOKUP: dict[str, ClientMsgType] = {m.value: m for m in ClientMsgType}


def parse_client_message(raw: str) -> tuple[ClientMsgType, dict]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"Invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ProtocolError("Message must be a JSON object")

    msg_type_str = data.get("type")
    if msg_type_str is None:
        raise ProtocolError("Message missing 'type' field")

    msg_type = _CLIENT_MSG_LOOKUP.get(msg_type_str)
    if msg_type is None:
        raise ProtocolError(f"Unknown message type: {msg_type_str}")

    payload = data.get("payload", {})
    if not isinstance(payload, dict):
        raise ProtocolError("Payload must be a JSON object")

    return msg_type, payload


def server_message(msg_type: ServerMsgType, payload: dict | None = None) -> str:
    return json.dumps({"type": msg_type.value, "payload": payload or {}})


def parse_cards_from_payload(payload: dict, key: str = "cards") -> list[Card]:
    raw_cards = payload.get(key)
    if not isinstance(raw_cards, list):
        raise ProtocolError(f"Expected list for '{key}'")
    try:
        return [Card(**c) for c in raw_cards]
    except Exception as exc:
        raise ProtocolError(f"Invalid card data: {exc}") from exc
