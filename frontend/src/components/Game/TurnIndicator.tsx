import { motion } from "framer-motion";

interface TurnIndicatorProps {
  currentPlayerSeat: number;
  yourSeat: number;
  playerNames: string[];
}

function relativePosition(seat: number, yourSeat: number): "you" | "left" | "partner" | "right" {
  const rel = (seat - yourSeat + 4) % 4;
  switch (rel) {
    case 0: return "you";
    case 1: return "left";
    case 2: return "partner";
    case 3: return "right";
    default: return "you";
  }
}

export default function TurnIndicator({
  currentPlayerSeat,
  yourSeat,
  playerNames,
}: TurnIndicatorProps) {
  const pos = relativePosition(currentPlayerSeat, yourSeat);
  const isYourTurn = pos === "you";
  const name = playerNames[currentPlayerSeat] ?? `Seat ${currentPlayerSeat}`;

  return (
    <motion.div
      layoutId="turn-indicator"
      className={`absolute z-30 pointer-events-none ${isYourTurn ? "bottom-0 left-1/2 -translate-x-1/2 mb-1" : "top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"}`}
      initial={false}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      <div
        className={`px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap
          ${isYourTurn
            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
            : "bg-gray-700/80 text-gray-300 border border-gray-600"
          }`}
      >
        {isYourTurn ? "Your Turn" : `${name}'s turn`}
      </div>
    </motion.div>
  );
}
