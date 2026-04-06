import type { Card, Suit } from "../types/game";

export const RANK_NAMES: Record<number, string> = {
  11: "J",
  12: "Q",
  13: "K",
  14: "A",
};

export const WISH_RANKS = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14];

const SUIT_COLORS: Record<string, string> = {
  jade: "#22c55e",
  sword: "#3b82f6",
  pagoda: "#f97316",
  star: "#eab308",
  special: "#a855f7",
};

const SUIT_SYMBOLS: Record<string, string> = {
  jade: "\u2663",
  sword: "\u2694",
  pagoda: "\u2666",
  star: "\u2605",
};

const SPECIAL_IMAGES: Record<string, string> = {
  dragon: "/cards/special/dragon.png",
  phoenix: "/cards/special/phoenix.png",
  hound: "/cards/special/dog.png",
  mah_jong: "/cards/special/Mahjong.png",
};

export function cardSortKey(card: Card): number {
  if (card.special === "hound") return 0.5;
  if (card.special === "mah_jong") return 1.0;
  if (card.special === "phoenix") return 14.5;
  if (card.special === "dragon") return 15.0;
  return card.rank ?? 0;
}

export function sortHand(cards: Card[]): Card[] {
  return [...cards].sort((a, b) => cardSortKey(a) - cardSortKey(b));
}

export function cardDisplayRank(card: Card): string {
  if (card.special) {
    return card.special.charAt(0).toUpperCase() + card.special.slice(1);
  }
  if (card.rank === null) return "";
  return RANK_NAMES[card.rank] ?? String(card.rank);
}

export function cardDisplayName(card: Card): string {
  if (card.special) {
    const name = card.special.replace("_", " ");
    return name.charAt(0).toUpperCase() + name.slice(1);
  }
  const rank = cardDisplayRank(card);
  const suit = card.suit.charAt(0).toUpperCase() + card.suit.slice(1);
  return `${rank} of ${suit}`;
}

export function suitColor(suit: Suit): string {
  return SUIT_COLORS[suit] ?? "#9ca3af";
}

export function suitSymbol(suit: Suit): string {
  return SUIT_SYMBOLS[suit] ?? "";
}

export function specialImage(special: string): string | null {
  return SPECIAL_IMAGES[special] ?? null;
}

export function isSpecialCard(card: Card): boolean {
  return card.special !== null;
}

export function cardKey(card: Card): string {
  if (card.special) return `special-${card.special}`;
  return `${card.suit}-${card.rank}`;
}

export function cardsEqual(a: Card, b: Card): boolean {
  return a.suit === b.suit && a.rank === b.rank && a.special === b.special;
}

export function cardInList(card: Card, list: Card[]): boolean {
  return list.some((c) => cardsEqual(c, card));
}

export function wishRankDisplay(rank: number): string {
  return RANK_NAMES[rank] ?? String(rank);
}
