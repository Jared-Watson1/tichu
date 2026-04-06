import { wishRankDisplay } from "../../utils/cardUtils";

interface WishIndicatorProps {
  activeWish: number | null;
}

export default function WishIndicator({ activeWish }: WishIndicatorProps) {
  if (activeWish === null) return null;

  return (
    <div
      className="absolute top-2 left-1/2 -translate-x-1/2 z-10
        px-3 py-1 rounded-full bg-amber-500/20 border border-amber-500/40
        text-amber-400 text-xs font-bold animate-pulse"
    >
      Wish: {wishRankDisplay(activeWish)}
    </div>
  );
}
