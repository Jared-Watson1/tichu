import { useState } from "react";
import type { Card as CardType } from "../../types/game";
import { useWS } from "../../contexts/WebSocketContext";
import { useGameStore } from "../../stores/gameStore";
import { cardKey, cardsEqual, sortHand } from "../../utils/cardUtils";
import Card from "../Card/Card";

interface CardPushProps {
  hand: CardType[];
}

export default function CardPush({ hand }: CardPushProps) {
  const { actions } = useWS();
  const gameState = useGameStore((s) => s.gameState);
  const yourSeat = gameState?.your_seat ?? 0;

  const leftOpp = (yourSeat + 1) % 4;
  const partner = (yourSeat + 2) % 4;
  const rightOpp = (yourSeat + 3) % 4;

  const targets = [
    { seat: leftOpp, label: gameState?.players[leftOpp]?.name ?? "Left" },
    { seat: partner, label: gameState?.players[partner]?.name ?? "Partner" },
    { seat: rightOpp, label: gameState?.players[rightOpp]?.name ?? "Right" },
  ];

  const [assignments, setAssignments] = useState<Record<number, CardType>>({});
  const [selectedCard, setSelectedCard] = useState<CardType | null>(null);

  const assignedCards = Object.values(assignments);
  const sorted = sortHand(hand);

  const isAssigned = (card: CardType) =>
    assignedCards.some((c) => cardsEqual(c, card));

  const handleCardClick = (card: CardType) => {
    if (isAssigned(card)) {
      const newAssignments = { ...assignments };
      for (const [seat, c] of Object.entries(newAssignments)) {
        if (cardsEqual(c, card)) {
          delete newAssignments[Number(seat)];
        }
      }
      setAssignments(newAssignments);
      setSelectedCard(null);
      return;
    }
    setSelectedCard(card);
  };

  const handleSlotClick = (seat: number) => {
    if (!selectedCard) return;
    if (isAssigned(selectedCard)) return;

    const newAssignments = { ...assignments, [seat]: selectedCard };
    setAssignments(newAssignments);
    setSelectedCard(null);
  };

  const canConfirm = targets.every(({ seat }) => assignments[seat] !== undefined);

  const handleConfirm = () => {
    if (!canConfirm) return;
    const pushMap: Record<number, CardType> = {};
    for (const { seat } of targets) {
      pushMap[seat] = assignments[seat];
    }
    actions.pushCards(pushMap);
  };

  return (
    <div className="flex flex-col items-center gap-4 w-full">
      <div className="text-amber-400 text-sm font-semibold">
        Select a card, then click a player to assign it
      </div>

      <div className="flex gap-4 justify-center">
        {targets.map(({ seat, label }) => {
          const card = assignments[seat];
          return (
            <button
              key={seat}
              type="button"
              onClick={() => handleSlotClick(seat)}
              className={`flex flex-col items-center gap-1 p-2 rounded-lg border-2
                transition-colors min-w-[80px]
                ${card ? "border-emerald-500/50 bg-emerald-500/10" : "border-dashed border-gray-600 bg-gray-800/30"}
                ${selectedCard && !card ? "hover:border-amber-400 cursor-pointer" : "cursor-default"}`}
            >
              <span className="text-xs text-gray-400">{label}</span>
              {card ? (
                <Card card={card} size="sm" />
              ) : (
                <div className="w-12 h-[68px] rounded border border-dashed border-gray-600 opacity-40" />
              )}
            </button>
          );
        })}
      </div>

      <div className="flex items-end justify-center flex-wrap gap-1">
        {sorted.map((card) => {
          const assigned = isAssigned(card);
          const isSelected = selectedCard && cardsEqual(selectedCard, card);
          return (
            <div
              key={cardKey(card)}
              className={assigned && !isSelected ? "opacity-30" : ""}
            >
              <Card
                card={card}
                size="md"
                selected={!!isSelected}
                onClick={() => handleCardClick(card)}
              />
            </div>
          );
        })}
      </div>

      <button
        type="button"
        onClick={handleConfirm}
        disabled={!canConfirm}
        className="px-6 py-2.5 rounded-lg bg-emerald-500 text-white font-bold
          hover:bg-emerald-400 disabled:opacity-30 disabled:cursor-not-allowed
          transition-colors min-h-[44px]"
      >
        Confirm Push
      </button>
    </div>
  );
}
