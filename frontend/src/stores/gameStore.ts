import { create } from "zustand";
import type { GameState, TrickEntry } from "../types/game";

export type AppPhase = "lobby" | "waiting" | "playing";
export type ConnectionStatus = "disconnected" | "connecting" | "connected";

export interface GameLogEntry {
  type: string;
  message: string;
  timestamp: number;
  seat?: number;
}

export interface TrickHistoryEntry {
  winner: number;
  cards: TrickEntry[];
  trickNumber: number;
}

interface GameStore {
  gameState: GameState | null;
  gameId: string | null;
  playerId: string | null;
  playerName: string | null;
  phase: AppPhase;
  connectionStatus: ConnectionStatus;
  lobbyPlayers: Record<number, string>;
  errorMessage: string | null;
  gameLog: GameLogEntry[];

  // animation state
  lastTrickWinner: number | null;
  trickHistory: TrickHistoryEntry[];
  roundScoreHistory: Array<[number, number]>;
  soundEnabled: boolean;

  setGameState: (state: GameState) => void;
  setGameId: (id: string) => void;
  setPlayerId: (id: string) => void;
  setPlayerName: (name: string) => void;
  setPhase: (phase: AppPhase) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  setLobbyPlayers: (players: Record<number, string>) => void;
  addLobbyPlayer: (seat: number, name: string) => void;
  setError: (message: string | null) => void;
  addLogEntry: (type: string, message: string, seat?: number) => void;
  clearLog: () => void;
  setLastTrickWinner: (seat: number | null) => void;
  addTrickHistory: (entry: TrickHistoryEntry) => void;
  clearTrickHistory: () => void;
  addRoundScore: (scores: [number, number]) => void;
  setSoundEnabled: (enabled: boolean) => void;
  reset: () => void;
}

export const useGameStore = create<GameStore>((set) => ({
  gameState: null,
  gameId: null,
  playerId: null,
  playerName: null,
  phase: "lobby",
  connectionStatus: "disconnected",
  lobbyPlayers: {},
  errorMessage: null,
  gameLog: [],
  lastTrickWinner: null,
  trickHistory: [],
  roundScoreHistory: [],
  soundEnabled: localStorage.getItem("tichu_sound") !== "false",

  setGameState: (state) => set({ gameState: state }),
  setGameId: (id) => set({ gameId: id }),
  setPlayerId: (id) => set({ playerId: id }),
  setPlayerName: (name) => set({ playerName: name }),
  setPhase: (phase) => set({ phase }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
  setLobbyPlayers: (players) => set({ lobbyPlayers: players }),
  addLobbyPlayer: (seat, name) =>
    set((s) => ({ lobbyPlayers: { ...s.lobbyPlayers, [seat]: name } })),
  setError: (message) => set({ errorMessage: message }),
  addLogEntry: (type, message, seat) =>
    set((s) => ({
      gameLog: [
        ...s.gameLog.slice(-99),
        { type, message, timestamp: Date.now(), seat },
      ],
    })),
  clearLog: () => set({ gameLog: [] }),
  setLastTrickWinner: (seat) => set({ lastTrickWinner: seat }),
  addTrickHistory: (entry) =>
    set((s) => ({ trickHistory: [...s.trickHistory, entry] })),
  clearTrickHistory: () => set({ trickHistory: [] }),
  addRoundScore: (scores) =>
    set((s) => ({ roundScoreHistory: [...s.roundScoreHistory, scores] })),
  setSoundEnabled: (enabled) => {
    localStorage.setItem("tichu_sound", String(enabled));
    set({ soundEnabled: enabled });
  },
  reset: () =>
    set({
      gameState: null,
      gameId: null,
      playerId: null,
      playerName: null,
      phase: "lobby",
      connectionStatus: "disconnected",
      lobbyPlayers: {},
      errorMessage: null,
      gameLog: [],
      lastTrickWinner: null,
      trickHistory: [],
      roundScoreHistory: [],
    }),
}));
