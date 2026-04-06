import { motion } from "framer-motion";
import type { Card as CardType } from "../../types/game";
import {
  cardDisplayRank,
  specialImage,
  suitColor,
  suitSymbol,
} from "../../utils/cardUtils";
import { cardSpring } from "../../utils/animationConfig";

interface CardProps {
  card: CardType;
  selected?: boolean;
  onClick?: () => void;
  size?: "sm" | "md" | "lg";
  faceDown?: boolean;
  className?: string;
  layoutId?: string;
  animate?: boolean;
}

const SIZES = {
  sm: { w: 48, h: 68, text: "text-xs", symbol: "text-lg", corner: "text-[8px]" },
  md: { w: 64, h: 90, text: "text-sm", symbol: "text-2xl", corner: "text-[10px]" },
  lg: { w: 80, h: 112, text: "text-base", symbol: "text-3xl", corner: "text-xs" },
};

export default function Card({
  card,
  selected = false,
  onClick,
  size = "md",
  faceDown = false,
  className = "",
  layoutId,
  animate: shouldAnimate = true,
}: CardProps) {
  const dim = SIZES[size];

  if (faceDown) {
    return (
      <div
        className={`rounded-lg border-2 border-gray-600 flex items-center justify-center
          bg-gradient-to-br from-gray-700 to-gray-800 shadow-md cursor-default
          select-none shrink-0 ${className}`}
        style={{ width: dim.w, height: dim.h }}
      >
        <div className="w-[60%] h-[70%] rounded border border-gray-500 bg-gray-600/50" />
      </div>
    );
  }

  const isSpecial = card.special !== null;
  const imgSrc = isSpecial ? specialImage(card.special!) : null;

  const motionProps = shouldAnimate
    ? {
        layout: true as const,
        layoutId,
        animate: { y: selected ? -12 : 0 },
        transition: cardSpring,
        whileHover: onClick ? { y: selected ? -12 : -4 } : undefined,
        whileTap: onClick ? { scale: 0.97 } : undefined,
      }
    : {};

  if (isSpecial && imgSrc) {
    return (
      <motion.button
        type="button"
        onClick={onClick}
        {...motionProps}
        className={`rounded-lg border-2 overflow-hidden shadow-md
          select-none shrink-0
          ${selected ? "ring-2 ring-amber-400 border-amber-400" : "border-gray-500"}
          ${onClick ? "cursor-pointer" : "cursor-default"}
          ${className}`}
        style={{ width: dim.w, height: dim.h }}
      >
        <img
          src={imgSrc}
          alt={card.special ?? ""}
          className="w-full h-full object-cover"
          draggable={false}
        />
      </motion.button>
    );
  }

  const color = suitColor(card.suit);
  const symbol = suitSymbol(card.suit);
  const rank = cardDisplayRank(card);

  return (
    <motion.button
      type="button"
      onClick={onClick}
      {...motionProps}
      className={`rounded-lg border-2 relative overflow-hidden shadow-md
        bg-gradient-to-br from-white to-gray-100
        select-none shrink-0 flex flex-col
        ${selected ? "ring-2 ring-amber-400 border-amber-400" : ""}
        ${onClick ? "cursor-pointer" : "cursor-default"}
        ${className}`}
      style={{
        width: dim.w,
        height: dim.h,
        borderColor: selected ? undefined : color,
      }}
    >
      <div
        className={`absolute top-0.5 left-1 leading-tight font-bold ${dim.corner}`}
        style={{ color }}
      >
        <div>{rank}</div>
        <div className="-mt-0.5">{symbol}</div>
      </div>

      <div
        className={`flex-1 flex items-center justify-center ${dim.symbol} leading-none`}
        style={{ color }}
      >
        {symbol}
      </div>

      <div
        className={`absolute bottom-0.5 right-1 leading-tight font-bold rotate-180 ${dim.corner}`}
        style={{ color }}
      >
        <div>{rank}</div>
        <div className="-mt-0.5">{symbol}</div>
      </div>
    </motion.button>
  );
}
