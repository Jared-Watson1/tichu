import { useState } from "react";
import { WebSocketProvider } from "./contexts/WebSocketContext";
import { useGameStore } from "./stores/gameStore";
import CreateGame from "./components/Lobby/CreateGame";
import JoinGame from "./components/Lobby/JoinGame";
import WaitingRoom from "./components/Lobby/WaitingRoom";
import GameBoard from "./components/Game/GameBoard";

function AppContent() {
  const phase = useGameStore((s) => s.phase);
  const connectionStatus = useGameStore((s) => s.connectionStatus);
  const [tab, setTab] = useState<"create" | "join">("create");

  if (phase === "playing") {
    return <GameBoard />;
  }

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
      <h1 className="text-5xl font-bold text-white mb-2 tracking-tight">
        Tichu
      </h1>
      <p className="text-gray-500 text-sm mb-8">Online Card Game</p>

      {connectionStatus === "connecting" && (
        <div className="text-amber-400 text-sm mb-4 animate-pulse">
          Connecting to server...
        </div>
      )}
      {connectionStatus === "disconnected" && (
        <div className="text-red-400 text-sm mb-4">
          Disconnected. Reconnecting...
        </div>
      )}

      {phase === "lobby" && (
        <div className="w-full max-w-sm">
          <div className="flex mb-6 bg-gray-800 rounded-lg p-1">
            <button
              type="button"
              onClick={() => setTab("create")}
              className={`flex-1 py-2 rounded-md text-sm font-semibold transition-colors
                ${tab === "create"
                  ? "bg-gray-700 text-white"
                  : "text-gray-400 hover:text-gray-200"
                }`}
            >
              Create
            </button>
            <button
              type="button"
              onClick={() => setTab("join")}
              className={`flex-1 py-2 rounded-md text-sm font-semibold transition-colors
                ${tab === "join"
                  ? "bg-gray-700 text-white"
                  : "text-gray-400 hover:text-gray-200"
                }`}
            >
              Join
            </button>
          </div>
          {tab === "create" ? <CreateGame /> : <JoinGame />}
        </div>
      )}

      {phase === "waiting" && <WaitingRoom />}
    </div>
  );
}

export default function App() {
  return (
    <WebSocketProvider>
      <AppContent />
    </WebSocketProvider>
  );
}
