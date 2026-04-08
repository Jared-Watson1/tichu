import asyncio
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket

from lobby.manager import LobbyManager
from ws.handler import websocket_handler

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="Tichu Backend")
lobby_manager = LobbyManager()


async def _cleanup_loop() -> None:
    while True:
        await asyncio.sleep(300)
        removed = lobby_manager.cleanup_stale_rooms(max_age_seconds=7200)
        if removed:
            logger.info("Cleaned up %d stale room(s)", removed)


@app.on_event("startup")
async def startup() -> None:
    asyncio.create_task(_cleanup_loop())


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket_handler(websocket, lobby_manager)
