from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket

from lobby.manager import LobbyManager
from ws.handler import websocket_handler

load_dotenv()

app = FastAPI(title="Tichu Backend")
lobby_manager = LobbyManager()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket_handler(websocket, lobby_manager)
