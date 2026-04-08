import { motion } from "framer-motion";
import type { PlayerPublicInfo } from "../../types/game";

interface OpponentHandProps {
  player: PlayerPublicInfo;
  position: "top" | "left" | "right";
  isCurrentTurn?: boolean;
  isTeammate?: boolean;
  outOrder?: number[];
}

const POSITION_LABELS: Record<number, string> = {
  1: "1st",
  2: "2nd",
  3: "3rd",
  4: "4th",
};

export default function OpponentHand({
  player,
  isCurrentTurn = false,
  isTeammate = false,
  outOrder = [],
}: OpponentHandProps) {
  const cardCount = player.card_count;
  const isOut = player.has_gone_out;
  const tichu = player.called_tichu;
  const outPosition = outOrder.indexOf(player.seat) + 1;

  return (
    <div className="flex flex-col items-center gap-1.5 relative">
      {/* name + tichu badge row */}
      <div className="flex items-center gap-1.5">
        <span
          className={`text-xs font-semibold truncate max-w-[90px]
            ${isCurrentTurn ? "text-emerald-400" : "text-gray-400"}`}
        >
          {player.name}
        </span>
        {tichu && (
          <span
            className={`text-[9px] font-bold px-1.5 py-0.5 rounded
              ${tichu === "grand" ? "bg-red-500/20 text-red-400" : "bg-amber-500/20 text-amber-400"}`}
          >
            {tichu === "grand" ? "GT" : "T"}
          </span>
        )}
      </div>

      {/* card count or out indicator */}
      {isOut ? (
        <div className="flex items-center gap-1.5">
          <span
            className={`text-sm font-bold px-2.5 py-1 rounded-lg
              ${outPosition === 1
                ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                : outPosition === 2
                  ? "bg-gray-500/20 text-gray-300 border border-gray-500/30"
                  : "bg-gray-700/50 text-gray-500 border border-gray-600/30"
              }`}
          >
            {POSITION_LABELS[outPosition] ?? "Out"}
          </span>
        </div>
      ) : (
        <motion.div
          className={`relative flex items-center justify-center rounded-xl border-2 px-3 py-2
            ${isCurrentTurn
              ? "border-emerald-500/60 bg-emerald-500/10"
              : isTeammate
                ? "border-emerald-700/30 bg-gray-800/50"
                : "border-gray-600/40 bg-gray-800/50"
            }`}
          animate={cardCount === 1 ? { borderColor: ["rgba(245,158,11,0.4)", "rgba(245,158,11,0.8)", "rgba(245,158,11,0.4)"] } : {}}
          transition={cardCount === 1 ? { duration: 1.5, repeat: Infinity } : {}}
        >
          <div className="flex items-center gap-2">
            {/* mini card back icon */}
            <div className="w-5 h-7 rounded border border-gray-500 bg-gradient-to-br from-gray-600 to-gray-700 shrink-0" />
            <span
              className={`text-xl font-bold tabular-nums
                ${cardCount <= 3 ? "text-amber-400" : "text-gray-200"}`}
            >
              {cardCount}
            </span>
          </div>

          {/* turn indicator dot */}
          {isCurrentTurn && (
            <motion.div
              className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-400"
              animate={{ scale: [1, 1.4, 1] }}
              transition={{ duration: 1.2, repeat: Infinity }}
            />
          )}
        </motion.div>
      )}
    </div>
  );
}
