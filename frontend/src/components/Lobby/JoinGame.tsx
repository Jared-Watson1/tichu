import { useEffect, useState } from "react";
import { useWS } from "../../contexts/WebSocketContext";
import { useGameStore } from "../../stores/gameStore";

export default function JoinGame() {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { actions } = useWS();
  const setPlayerName = useGameStore((s) => s.setPlayerName);
  const errorMessage = useGameStore((s) => s.errorMessage);

  useEffect(() => {
    if (errorMessage) setIsSubmitting(false);
  }, [errorMessage]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = name.trim();
    const trimmedCode = code.trim().toUpperCase();
    if (!trimmedName || !trimmedCode || isSubmitting) return;
    setIsSubmitting(true);
    setPlayerName(trimmedName);
    actions.joinGame(trimmedCode, trimmedName);
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <h2 className="text-xl font-semibold text-white">Join Game</h2>
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
      <input
        type="text"
        value={code}
        onChange={(e) => setCode(e.target.value.toUpperCase())}
        placeholder="Room code"
        maxLength={10}
        className="px-4 py-3 rounded-lg bg-gray-800 border border-gray-600
          text-white placeholder-gray-400 focus:outline-none focus:border-amber-400
          transition-colors font-mono tracking-widest"
      />
      {errorMessage && (
        <p className="text-red-400 text-sm">{errorMessage}</p>
      )}
      <button
        type="submit"
        disabled={!name.trim() || !code.trim() || isSubmitting}
        className="px-6 py-3 rounded-lg bg-emerald-500 text-white font-semibold
          hover:bg-emerald-400 disabled:opacity-40 disabled:cursor-not-allowed
          transition-colors"
      >
        {isSubmitting ? "Joining..." : "Join Game"}
      </button>
    </form>
  );
}
