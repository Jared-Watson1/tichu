from __future__ import annotations

import asyncio
import random
import string
import time
import uuid

from fastapi import WebSocket

from game.engine import TichuEngine
from game.models import GameState
from lobby.models import (
    DisconnectedPlayer,
    GameRoom,
    LobbyError,
    PlayerConnection,
)

RECONNECT_TIMEOUT = 60
ROOM_CODE_LENGTH = 6


class LobbyManager:

    def __init__(self) -> None:
        self._rooms: dict[str, GameRoom] = {}
        self._player_to_room: dict[str, str] = {}

    def create_game(self, player_name: str, websocket: WebSocket) -> tuple[str, str]:
        game_id = self._generate_room_code()
        player_id = str(uuid.uuid4())

        room = GameRoom(game_id=game_id)
        connection = PlayerConnection(
            player_id=player_id,
            player_name=player_name,
            game_id=game_id,
            seat=0,
            websocket=websocket,
        )
        room.players[0] = connection

        self._rooms[game_id] = room
        self._player_to_room[player_id] = game_id
        return game_id, player_id

    def add_ai_player(self, game_id: str) -> tuple[str, int]:
        room = self._rooms.get(game_id)
        if room is None:
            raise LobbyError(f"Room {game_id} not found")

        if room.game_state is not None:
            raise LobbyError("Game already started")

        if len(room.players) >= 4:
            raise LobbyError("Room is full")

        occupied_seats = set(room.players.keys())
        seat = next(s for s in range(4) if s not in occupied_seats)

        existing_ai_count = len(room.ai_seats)
        name = "Claude" if existing_ai_count == 0 else f"Claude {existing_ai_count + 1}"

        player_id = str(uuid.uuid4())
        connection = PlayerConnection(
            player_id=player_id,
            player_name=name,
            game_id=game_id,
            seat=seat,
            websocket=None,
        )
        room.players[seat] = connection
        room.ai_seats.add(seat)
        self._player_to_room[player_id] = game_id
        return player_id, seat

    def is_ai_seat(self, game_id: str, seat: int) -> bool:
        room = self._rooms.get(game_id)
        if room is None:
            return False
        return seat in room.ai_seats

    def join_game(
        self, game_id: str, player_name: str, websocket: WebSocket
    ) -> tuple[str, int]:
        room = self._rooms.get(game_id)
        if room is None:
            raise LobbyError(f"Room {game_id} not found")

        if room.game_state is not None:
            raise LobbyError("Game already started")

        if len(room.players) >= 4:
            raise LobbyError("Room is full")

        occupied_seats = set(room.players.keys())
        seat = next(s for s in range(4) if s not in occupied_seats)

        player_id = str(uuid.uuid4())
        connection = PlayerConnection(
            player_id=player_id,
            player_name=player_name,
            game_id=game_id,
            seat=seat,
            websocket=websocket,
        )
        room.players[seat] = connection
        self._player_to_room[player_id] = game_id
        return player_id, seat

    def start_game(self, game_id: str) -> GameState:
        room = self._rooms.get(game_id)
        if room is None:
            raise LobbyError(f"Room {game_id} not found")

        if len(room.players) != 4:
            raise LobbyError(f"Need 4 players to start, have {len(room.players)}")

        if room.game_state is not None:
            raise LobbyError("Game already started")

        players_info = []
        for seat in range(4):
            conn = room.players[seat]
            players_info.append({"id": conn.player_id, "name": conn.player_name})

        state = TichuEngine.create_game(game_id, players_info)
        TichuEngine.start_round(state)
        room.game_state = state
        return state

    def reconnect(
        self, game_id: str, player_id: str, websocket: WebSocket
    ) -> int:
        room = self._rooms.get(game_id)
        if room is None:
            raise LobbyError(f"Room {game_id} not found")

        dc_entry: DisconnectedPlayer | None = None
        dc_seat: int | None = None
        for seat, dc in room.disconnected_players.items():
            if dc.player_id == player_id:
                dc_entry = dc
                dc_seat = seat
                break

        if dc_entry is None:
            raise LobbyError("No disconnected player with that ID found")

        if dc_entry.reconnect_task is not None:
            dc_entry.reconnect_task.cancel()

        connection = PlayerConnection(
            player_id=player_id,
            player_name=dc_entry.player_name,
            game_id=game_id,
            seat=dc_seat,
            websocket=websocket,
        )
        room.players[dc_seat] = connection
        del room.disconnected_players[dc_seat]
        self._player_to_room[player_id] = game_id
        return dc_seat

    def get_room(self, game_id: str) -> GameRoom | None:
        return self._rooms.get(game_id)

    def get_player_room_and_seat(
        self, player_id: str
    ) -> tuple[GameRoom, int] | None:
        game_id = self._player_to_room.get(player_id)
        if game_id is None:
            return None
        room = self._rooms.get(game_id)
        if room is None:
            return None
        for seat, conn in room.players.items():
            if conn.player_id == player_id:
                return room, seat
        return None

    def get_all_connected(
        self, game_id: str
    ) -> list[tuple[int, WebSocket]]:
        room = self._rooms.get(game_id)
        if room is None:
            return []
        return [
            (seat, conn.websocket)
            for seat, conn in room.players.items()
            if conn.connected and conn.websocket is not None
        ]

    def handle_disconnect(self, player_id: str) -> str | None:
        """Handle player disconnect. Returns game_id if player was in a room."""
        game_id = self._player_to_room.get(player_id)
        if game_id is None:
            return None

        room = self._rooms.get(game_id)
        if room is None:
            return None

        seat: int | None = None
        conn: PlayerConnection | None = None
        for s, c in room.players.items():
            if c.player_id == player_id:
                seat = s
                conn = c
                break

        if seat is None or conn is None:
            return None

        del room.players[seat]
        del self._player_to_room[player_id]

        if room.game_state is None:
            return game_id

        dc = DisconnectedPlayer(
            player_id=player_id,
            player_name=conn.player_name,
            seat=seat,
            disconnect_time=time.time(),
        )
        dc.reconnect_task = asyncio.create_task(
            self._expire_player(game_id, seat)
        )
        room.disconnected_players[seat] = dc
        return game_id

    async def _expire_player(self, game_id: str, seat: int) -> None:
        await asyncio.sleep(RECONNECT_TIMEOUT)
        room = self._rooms.get(game_id)
        if room is None:
            return
        room.disconnected_players.pop(seat, None)

    def _generate_room_code(self) -> str:
        chars = string.ascii_uppercase + string.digits
        while True:
            code = "".join(random.choices(chars, k=ROOM_CODE_LENGTH))
            if code not in self._rooms:
                return code
