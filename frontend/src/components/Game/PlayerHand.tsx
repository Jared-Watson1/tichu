import { AnimatePresence, motion } from "framer-motion";
import type { Card as CardType } from "../../types/game";
import { cardKey, cardInList, cardsEqual, sortHand } from "../../utils/cardUtils";
import { cardSpring } from "../../utils/animationConfig";
import Card from "../Card/Card";

interface PlayerHandProps {
  cards: CardType[];
  selectedCards: CardType[];
  onSelectionChange: (cards: CardType[]) => void;
  disabled?: boolean;
}

export default function PlayerHand({
  cards,
  selectedCards,
  onSelectionChange,
  disabled = false,
}: PlayerHandProps) {
  const sorted = sortHand(cards);

  const toggleCard = (card: CardType) => {
    if (disabled) return;
    if (cardInList(card, selectedCards)) {
      onSelectionChange(selectedCards.filter((c) => !cardsEqual(c, card)));
    } else {
      onSelectionChange([...selectedCards, card]);
    }
  };

  const cardWidth = 64;
  const minOverlap = 20;
  const maxOverlap = 44;
  const totalCards = sorted.length;

  const availableWidth = Math.min(window.innerWidth - 32, 900);
  const neededWidth = cardWidth * totalCards;
  const overlap =
    totalCards <= 1
      ? 0
      : Math.min(
          maxOverlap,
          Math.max(minOverlap, (neededWidth - availableWidth) / (totalCards - 1)),
        );

  return (
    <div className="flex items-end justify-center w-full px-2">
      <div className="flex items-end" style={{ minHeight: 106 }}>
        <AnimatePresence mode="popLayout">
          {sorted.map((card, i) => (
            <motion.div
              key={cardKey(card)}
              layout
              initial={{ opacity: 0, y: 40, scale: 0.8 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -60, scale: 0.8 }}
              transition={cardSpring}
              style={{
                marginLeft: i === 0 ? 0 : -overlap,
                zIndex: i,
              }}
            >
              <Card
                card={card}
                size="md"
                selected={cardInList(card, selectedCards)}
                onClick={() => toggleCard(card)}
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
