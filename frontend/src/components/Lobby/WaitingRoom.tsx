import { useWS } from "../../contexts/WebSocketContext";
import { useGameStore } from "../../stores/gameStore";

const SEATS = [
  { seat: 0, team: "A", label: "Seat 1" },
  { seat: 1, team: "B", label: "Seat 2" },
  { seat: 2, team: "A", label: "Seat 3" },
  { seat: 3, team: "B", label: "Seat 4" },
];

export default function WaitingRoom() {
  const { actions } = useWS();
  const gameId = useGameStore((s) => s.gameId);
  const lobbyPlayers = useGameStore((s) => s.lobbyPlayers);

  const playerCount = Object.keys(lobbyPlayers).length;
  const canStart = playerCount === 4;

  const copyCode = () => {
    if (gameId) navigator.clipboard.writeText(gameId);
  };

  return (
    <div className="flex flex-col items-center gap-8 w-full max-w-md">
      <h2 className="text-2xl font-bold text-white">Waiting Room</h2>

      <div className="flex items-center gap-3">
        <span className="text-gray-400 text-sm">Room Code:</span>
        <button
          type="button"
          onClick={copyCode}
          className="px-4 py-2 rounded-lg bg-gray-800 border border-gray-600
            text-amber-400 font-mono text-2xl tracking-widest
            hover:bg-gray-700 transition-colors"
          title="Click to copy"
        >
          {gameId ?? "..."}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 w-full">
        {SEATS.map(({ seat, team, label }) => {
          const playerName = lobbyPlayers[seat];
          const filled = !!playerName;
          return (
            <div
              key={seat}
              className={`rounded-xl border-2 p-4 text-center transition-all
                ${filled
                  ? "border-emerald-500/50 bg-emerald-500/10"
                  : "border-gray-600 bg-gray-800/50"
                }`}
            >
              <div className="text-xs text-gray-400 mb-1">
                Team {team} {label}
              </div>
              {filled ? (
                <div className="text-white font-semibold">{playerName}</div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <div className="text-gray-500 animate-pulse">Waiting...</div>
                  <button
                    type="button"
                    onClick={() => actions.addAiPlayer()}
                    className="px-3 py-1 rounded-md bg-violet-600 text-white text-xs
                      font-medium hover:bg-violet-500 transition-colors"
                  >
                    Add AI
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="text-gray-400 text-sm">
        {playerCount}/4 players joined
      </div>

      <button
        type="button"
        onClick={() => actions.startGame()}
        disabled={!canStart}
        className="px-8 py-3 rounded-lg bg-amber-500 text-gray-900 font-bold text-lg
          hover:bg-amber-400 disabled:opacity-40 disabled:cursor-not-allowed
          transition-colors"
      >
        Start Game
      </button>
    </div>
  );
}
