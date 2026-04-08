import { useCallback, useEffect, useRef } from "react";
import { useGameStore } from "../stores/gameStore";
import type {
  CardsPlayedPayload,
  ErrorPayload,
  GameCreatedPayload,
  GameOverPayload,
  PlayerDisconnectedPayload,
  PlayerJoinedPayload,
  PlayerOutPayload,
  PlayerReconnectedPayload,
  RoundOverPayload,
  ServerMessage,
  TichuCalledPayload,
  WishMadePayload,
} from "../types/ws";
import type { GameState } from "../types/game";
import { wishRankDisplay } from "../utils/cardUtils";
import { TRICK_CLEAR_DELAY } from "../utils/animationConfig";

const WS_URL =
  import.meta.env.VITE_WS_URL ?? `ws://${window.location.host}/ws`;

const MAX_RECONNECT_DELAY = 30000;

function getPlayerName(seat: number): string {
  const state = useGameStore.getState();
  const gs = state.gameState;
  if (gs && gs.players[seat]) return gs.players[seat].name;
  const lobby = state.lobbyPlayers;
  if (lobby[seat]) return lobby[seat];
  return `Seat ${seat}`;
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectDelay = useRef(1000);
  const mountedRef = useRef(true);
  const trickClearTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const store = useGameStore;

  const handleMessage = useCallback((event: MessageEvent) => {
    let msg: ServerMessage;
    try {
      msg = JSON.parse(event.data);
    } catch {
      return;
    }

    const { type, payload } = msg;

    switch (type) {
      case "game_created": {
        const p = payload as unknown as GameCreatedPayload;
        store.getState().setGameId(p.game_id);
        store.getState().setPlayerId(p.player_id);
        store.getState().setPhase("waiting");
        store.getState().addLobbyPlayer(p.seat, store.getState().playerName ?? "You");
        sessionStorage.setItem("tichu_game_id", p.game_id);
        sessionStorage.setItem("tichu_player_id", p.player_id);
        break;
      }

      case "player_joined": {
        const p = payload as unknown as PlayerJoinedPayload;
        if (p.player_id) {
          store.getState().setPlayerId(p.player_id);
          sessionStorage.setItem("tichu_player_id", p.player_id);
          if (p.game_id) {
            store.getState().setGameId(p.game_id);
            sessionStorage.setItem("tichu_game_id", p.game_id);
          }
          store.getState().setPhase("waiting");
        }
        if (p.players) {
          const mapped: Record<number, string> = {};
          for (const [seat, name] of Object.entries(p.players)) {
            mapped[Number(seat)] = name;
          }
          store.getState().setLobbyPlayers(mapped);
        }
        if (p.player_name) {
          store.getState().addLobbyPlayer(p.seat, p.player_name);
        }
        break;
      }

      case "game_starting":
        store.getState().setPhase("playing");
        store.getState().clearTrickHistory();
        store.getState().addLogEntry("system", "Game starting");
        break;

      case "game_state": {
        const gs = payload as unknown as GameState;
        store.getState().setGameState(gs);
        store.getState().setPhase("playing");
        break;
      }

      case "cards_played": {
        const p = payload as unknown as CardsPlayedPayload;
        const name = getPlayerName(p.seat);
        store.getState().addLogEntry("play", `${name} played ${p.combination.type}`, p.seat);
        break;
      }

      case "player_passed": {
        const p = payload as unknown as PlayerDisconnectedPayload;
        const name = getPlayerName(p.seat);
        store.getState().addLogEntry("pass", `${name} passed`, p.seat);
        break;
      }

      case "trick_won": {
        const p = payload as unknown as PlayerDisconnectedPayload;
        const name = getPlayerName(p.seat);
        store.getState().addLogEntry("trick_won", `${name} won the trick`, p.seat);

        const currentTrick = store.getState().gameState?.trick;
        const history = store.getState().trickHistory;
        if (currentTrick && currentTrick.length > 0) {
          store.getState().addTrickHistory({
            winner: p.seat,
            cards: currentTrick,
            trickNumber: history.length + 1,
          });
        }

        store.getState().setLastTrickWinner(p.seat);
        if (trickClearTimer.current) clearTimeout(trickClearTimer.current);
        trickClearTimer.current = setTimeout(() => {
          store.getState().setLastTrickWinner(null);
        }, TRICK_CLEAR_DELAY);
        break;
      }

      case "tichu_called": {
        const p = payload as unknown as TichuCalledPayload;
        const name = getPlayerName(p.seat);
        const label = p.tichu_type === "grand" ? "Grand Tichu" : "Tichu";
        store.getState().addLogEntry("tichu", `${name} called ${label}`, p.seat);
        break;
      }

      case "wish_made": {
        const p = payload as unknown as WishMadePayload;
        store.getState().addLogEntry("wish", `Wish made for ${wishRankDisplay(p.rank)}`);
        break;
      }

      case "wish_fulfilled":
        store.getState().addLogEntry("wish", "Wish fulfilled");
        break;

      case "player_out": {
        const p = payload as unknown as PlayerOutPayload;
        const name = getPlayerName(p.seat);
        store.getState().addLogEntry("out", `${name} went out (#${p.position})`, p.seat);
        break;
      }

      case "round_over": {
        const p = payload as unknown as RoundOverPayload;
        store.getState().addLogEntry(
          "round",
          `Round ${p.round_number} over: ${p.scores[0]} - ${p.scores[1]}`,
        );
        store.getState().addRoundScore(p.scores);
        store.getState().clearTrickHistory();
        break;
      }

      case "game_over": {
        const p = payload as unknown as GameOverPayload;
        store.getState().addLogEntry(
          "game_over",
          `Game over! Team ${p.winning_team + 1} wins: ${p.final_scores[0]} - ${p.final_scores[1]}`,
        );
        break;
      }

      case "error": {
        const p = payload as unknown as ErrorPayload;
        store.getState().setError(p.message);
        store.getState().addLogEntry("error", p.message);
        break;
      }

      case "player_disconnected": {
        const p = payload as unknown as PlayerDisconnectedPayload;
        const name = getPlayerName(p.seat);
        store.getState().addLogEntry("system", `${name} disconnected`, p.seat);
        break;
      }

      case "player_reconnected": {
        const p = payload as unknown as PlayerReconnectedPayload;
        store.getState().addLogEntry("system", `${p.player_name} reconnected`, p.seat);
        break;
      }
    }
  }, [store]);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    store.getState().setConnectionStatus("connecting");
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      store.getState().setConnectionStatus("connected");
      reconnectDelay.current = 1000;

      const gameId = sessionStorage.getItem("tichu_game_id");
      const playerId = sessionStorage.getItem("tichu_player_id");
      const playerName = store.getState().playerName;
      if (gameId && playerId && playerName) {
        ws.send(
          JSON.stringify({
            type: "join_game",
            payload: {
              game_id: gameId,
              player_name: playerName,
              player_id: playerId,
            },
          }),
        );
        store.getState().setGameId(gameId);
        store.getState().setPlayerId(playerId);
        store.getState().setPhase("waiting");
      }
    };

    ws.onmessage = handleMessage;

    ws.onclose = () => {
      store.getState().setConnectionStatus("disconnected");
      if (mountedRef.current) {
        const jitter = 0.5 + Math.random() * 0.5;
        reconnectTimer.current = setTimeout(() => {
          reconnectDelay.current = Math.min(
            reconnectDelay.current * 2,
            MAX_RECONNECT_DELAY,
          );
          connect();
        }, reconnectDelay.current * jitter);
      }
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, [handleMessage, store]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (trickClearTimer.current) clearTimeout(trickClearTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((type: string, payload?: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, payload: payload ?? {} }));
    }
  }, []);

  return { send };
}
