from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from fastapi import WebSocket

from game.models import GameState


class LobbyError(Exception):
    pass


@dataclass
class PlayerConnection:
    player_id: str
    player_name: str
    game_id: str
    seat: int
    websocket: WebSocket | None
    connected: bool = True


@dataclass
class DisconnectedPlayer:
    player_id: str
    player_name: str
    seat: int
    disconnect_time: float
    reconnect_task: asyncio.Task | None = None


@dataclass
class GameRoom:
    game_id: str
    game_state: GameState | None = None
    players: dict[int, PlayerConnection] = field(default_factory=dict)
    disconnected_players: dict[int, DisconnectedPlayer] = field(default_factory=dict)
    ai_seats: set[int] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
