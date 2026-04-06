import { AnimatePresence, motion } from "framer-motion";
import type { TrickEntry } from "../../types/game";
import { cardSpring, SEAT_OFFSETS } from "../../utils/animationConfig";
import CardStack from "../Card/CardStack";

interface TrickAreaProps {
  trick: TrickEntry[];
  yourSeat: number;
  lastTrickWinner?: number | null;
}

function seatPosition(
  seat: number,
  yourSeat: number,
): "bottom" | "top" | "left" | "right" {
  const relative = (seat - yourSeat + 4) % 4;
  switch (relative) {
    case 0:
      return "bottom";
    case 1:
      return "left";
    case 2:
      return "top";
    case 3:
      return "right";
    default:
      return "bottom";
  }
}

const POSITION_CLASSES: Record<string, string> = {
  bottom: "bottom-2 left-1/2 -translate-x-1/2",
  top: "top-2 left-1/2 -translate-x-1/2",
  left: "left-2 top-1/2 -translate-y-1/2",
  right: "right-2 top-1/2 -translate-y-1/2",
};

export default function TrickArea({ trick, yourSeat, lastTrickWinner }: TrickAreaProps) {
  if (trick.length === 0 && lastTrickWinner === undefined) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <div className="w-20 h-28 rounded-lg border-2 border-dashed border-gray-700 opacity-30" />
      </div>
    );
  }

  const winnerPos = lastTrickWinner !== null && lastTrickWinner !== undefined
    ? seatPosition(lastTrickWinner, yourSeat)
    : null;

  const exitTarget = winnerPos ? SEAT_OFFSETS[winnerPos] : { x: 0, y: 0 };

  return (
    <div className="w-full h-full relative">
      <AnimatePresence mode="popLayout">
        {trick.map((entry) => {
          const pos = seatPosition(entry.seat, yourSeat);
          const origin = SEAT_OFFSETS[pos];
          return (
            <motion.div
              key={`trick-${entry.seat}`}
              className={`absolute ${POSITION_CLASSES[pos]}`}
              initial={{ opacity: 0, x: origin.x, y: origin.y, scale: 0.7 }}
              animate={{ opacity: 1, x: 0, y: 0, scale: 1 }}
              exit={{
                opacity: 0,
                x: exitTarget.x,
                y: exitTarget.y,
                scale: 0.6,
              }}
              transition={cardSpring}
            >
              <CardStack
                cards={entry.combination.cards}
                size="sm"
                overlap={20}
              />
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
