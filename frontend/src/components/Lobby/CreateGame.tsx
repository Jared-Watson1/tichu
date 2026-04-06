import { useState } from "react";
import { useWS } from "../../contexts/WebSocketContext";
import { useGameStore } from "../../stores/gameStore";

export default function CreateGame() {
  const [name, setName] = useState("");
  const { actions } = useWS();
  const setPlayerName = useGameStore((s) => s.setPlayerName);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    setPlayerName(trimmed);
    actions.createGame(trimmed);
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <h2 className="text-xl font-semibold text-white">Create Game</h2>
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Your name"
        maxLength={20}
        className="px-4 py-3 rounded-lg bg-gray-800 border border-gray-600
          text-white placeholder-gray-400 focus:outline-none focus:border-amber-400
          transition-colors"
      />
      <button
        type="submit"
        disabled={!name.trim()}
        className="px-6 py-3 rounded-lg bg-amber-500 text-gray-900 font-semibold
          hover:bg-amber-400 disabled:opacity-40 disabled:cursor-not-allowed
          transition-colors"
      >
        Create Game
      </button>
    </form>
  );
}
