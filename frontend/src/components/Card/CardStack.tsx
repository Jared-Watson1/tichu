import type { Card as CardType } from "../../types/game";
import { cardKey, cardInList } from "../../utils/cardUtils";
import Card from "./Card";

interface CardStackProps {
  cards: CardType[];
  overlap?: number;
  onCardClick?: (card: CardType, index: number) => void;
  selectedCards?: CardType[];
  size?: "sm" | "md" | "lg";
  faceDown?: boolean;
  className?: string;
}

export default function CardStack({
  cards,
  overlap = 30,
  onCardClick,
  selectedCards = [],
  size = "md",
  faceDown = false,
  className = "",
}: CardStackProps) {
  return (
    <div className={`flex items-end ${className}`}>
      {cards.map((card, i) => (
        <div
          key={cardKey(card)}
          style={{
            marginLeft: i === 0 ? 0 : -overlap,
            zIndex: i,
          }}
        >
          <Card
            card={card}
            size={size}
            faceDown={faceDown}
            selected={cardInList(card, selectedCards)}
            onClick={onCardClick ? () => onCardClick(card, i) : undefined}
          />
        </div>
      ))}
    </div>
  );
}
