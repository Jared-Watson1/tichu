import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useWS } from "../../contexts/WebSocketContext";
import { useGameStore } from "../../stores/gameStore";

const TEAM_SEATS: Record<string, number[]> = {
  A: [0, 2],
  B: [1, 3],
};

export default function WaitingRoom() {
  const { actions } = useWS();
  const gameId = useGameStore((s) => s.gameId);
  const lobbyPlayers = useGameStore((s) => s.lobbyPlayers);

  const [copied, setCopied] = useState(false);
  const [teamsRevealed, setTeamsRevealed] = useState(false);
  const copyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const revealTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const playerCount = Object.keys(lobbyPlayers).length;
  const allJoined = playerCount === 4;

  useEffect(() => {
    if (allJoined && !teamsRevealed) {
      revealTimeoutRef.current = setTimeout(() => setTeamsRevealed(true), 600);
    }
    return () => {
      if (revealTimeoutRef.current) clearTimeout(revealTimeoutRef.current);
    };
  }, [allJoined, teamsRevealed]);

  const copyCode = () => {
    if (!gameId) return;
    navigator.clipboard.writeText(gameId);
    setCopied(true);
    if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
    copyTimeoutRef.current = setTimeout(() => setCopied(false), 2000);
  };

  const teamAPlayers = TEAM_SEATS.A.map((s) => lobbyPlayers[s]).filter(Boolean);
  const teamBPlayers = TEAM_SEATS.B.map((s) => lobbyPlayers[s]).filter(Boolean);

  return (
    <motion.div
      className="flex flex-col items-center gap-8 w-full max-w-md"
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.3 }}
    >
      <h2 className="text-2xl font-bold text-white">Waiting Room</h2>

      {/* Room code */}
      <div className="flex items-center gap-3">
        <span className="text-gray-400 text-sm">Room Code:</span>
        <button
          type="button"
          onClick={copyCode}
          className="relative px-4 py-2 rounded-lg bg-gray-800 border border-gray-600
            text-amber-400 font-mono text-2xl tracking-widest
            hover:bg-gray-700 transition-colors"
          title="Click to copy"
        >
          {gameId ?? "..."}
          <AnimatePresence>
            {copied && (
              <motion.span
                key="copied"
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: -28 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="absolute left-1/2 -translate-x-1/2 text-xs font-sans font-medium
                  text-emerald-400 pointer-events-none whitespace-nowrap"
              >
                Copied!
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>

      {/* Player list */}
      {!teamsRevealed && (
        <div className="w-full flex flex-col gap-2">
          <div className="text-gray-400 text-sm text-center mb-1">
            {playerCount}/4 players joined
          </div>

          <AnimatePresence initial={false}>
            {Object.entries(lobbyPlayers).map(([seat, name]) => (
              <motion.div
                key={seat}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
                className="flex items-center gap-3 px-4 py-3 rounded-xl
                  bg-emerald-500/10 border border-emerald-500/30"
              >
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                <span className="text-white font-semibold">{name}</span>
              </motion.div>
            ))}
          </AnimatePresence>

          {Array.from({ length: 4 - playerCount }).map((_, i) => (
            <div
              key={`empty-${i}`}
              className="flex items-center gap-3 px-4 py-3 rounded-xl
                bg-gray-800/50 border border-gray-700"
            >
              <div className="w-2 h-2 rounded-full bg-gray-600 animate-pulse" />
              <span className="text-gray-500 text-sm">Waiting...</span>
            </div>
          ))}

          {playerCount < 4 && (
            <button
              type="button"
              onClick={() => actions.addAiPlayer()}
              className="mt-2 px-4 py-2 rounded-lg bg-violet-600 text-white text-sm
                font-medium hover:bg-violet-500 transition-colors self-center"
            >
              Add AI Player
            </button>
          )}
        </div>
      )}

      {/* Team reveal */}
      {teamsRevealed && (
        <div className="w-full">
          <motion.p
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center text-gray-400 text-sm mb-5"
          >
            Teams have been set
          </motion.p>

          <div className="grid grid-cols-2 gap-4">
            {(["A", "B"] as const).map((team, teamIndex) => {
              const players = team === "A" ? teamAPlayers : teamBPlayers;
              return (
                <motion.div
                  key={team}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: teamIndex * 0.2, duration: 0.4 }}
                  className="flex flex-col gap-3 p-4 rounded-xl
                    bg-gray-800/60 border border-gray-700"
                >
                  <div className="text-center text-xs font-bold tracking-widest uppercase text-gray-400">
                    Team {team}
                  </div>
                  {players.map((name, i) => (
                    <motion.div
                      key={name}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: teamIndex * 0.2 + i * 0.15 + 0.2 }}
                      className={`text-center py-2 px-3 rounded-lg font-semibold text-sm
                        ${team === "A"
                          ? "bg-sky-500/15 text-sky-300 border border-sky-500/30"
                          : "bg-rose-500/15 text-rose-300 border border-rose-500/30"
                        }`}
                    >
                      {name}
                    </motion.div>
                  ))}
                </motion.div>
              );
            })}
          </div>

          <motion.button
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            type="button"
            onClick={() => actions.startGame()}
            className="mt-6 w-full px-8 py-3 rounded-lg bg-amber-500 text-gray-900
              font-bold text-lg hover:bg-amber-400 transition-colors"
          >
            Start Game
          </motion.button>
        </div>
      )}
    </motion.div>
  );
}
