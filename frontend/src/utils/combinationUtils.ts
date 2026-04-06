import type { Card, Combination, CombinationType } from "../types/game";

const MIN_STRAIGHT_LENGTH = 5;
const MIN_PAIR_SEQUENCE_PAIRS = 2;

function makeCombination(
  type: CombinationType,
  cards: Card[],
  rank: number,
  length: number,
  isBomb = false,
): Combination {
  return { type, cards, rank, length, is_bomb: isBomb };
}

function isConsecutive(sortedRanks: number[]): boolean {
  for (let i = 1; i < sortedRanks.length; i++) {
    if (sortedRanks[i] - sortedRanks[i - 1] !== 1) return false;
  }
  return true;
}

function fitPhoenixInStraight(
  ranks: number[],
): [number, number] | null {
  if (ranks.length === 0) return null;
  const sorted = [...ranks].sort((a, b) => a - b);
  const n = sorted.length;

  if (new Set(sorted).size !== n) return null;

  const gaps: number[] = [];
  for (let i = 1; i < n; i++) {
    const diff = sorted[i] - sorted[i - 1];
    if (diff === 1) continue;
    if (diff === 2) gaps.push(i);
    else return null;
  }

  if (gaps.length === 0) {
    const high = sorted[n - 1] + 1;
    if (high > 14) return [sorted[n - 1], n + 1];
    return [high, n + 1];
  }
  if (gaps.length === 1) {
    return [sorted[n - 1], n + 1];
  }
  return null;
}

function detectSingle(card: Card): Combination {
  if (card.special === "hound") {
    return makeCombination("hound_lead", [card], 0, 1);
  }
  if (card.special === "dragon") {
    return makeCombination("single", [card], 15.0, 1);
  }
  if (card.special === "phoenix") {
    return makeCombination("single", [card], 14.5, 1);
  }
  if (card.special === "mah_jong") {
    return makeCombination("single", [card], 1.0, 1);
  }
  return makeCombination("single", [card], card.rank ?? 0, 1);
}

function detectBomb(
  allCards: Card[],
  normalCards: Card[],
  hasPhoenix: boolean,
): Combination | null {
  if (hasPhoenix) return null;
  const n = allCards.length;
  const nonSpecial = normalCards.filter((c) => c.special === null);

  if (n === 4 && nonSpecial.length === 4) {
    const ranks = new Set(nonSpecial.map((c) => c.rank));
    if (ranks.size === 1) {
      return makeCombination(
        "four_bomb",
        allCards,
        nonSpecial[0].rank ?? 0,
        4,
        true,
      );
    }
  }

  if (n >= MIN_STRAIGHT_LENGTH && nonSpecial.length === n) {
    const suits = new Set(nonSpecial.map((c) => c.suit));
    if (suits.size === 1) {
      const sortedRanks = nonSpecial.map((c) => c.rank!).sort((a, b) => a - b);
      if (isConsecutive(sortedRanks)) {
        return makeCombination(
          "straight_bomb",
          allCards,
          sortedRanks[sortedRanks.length - 1],
          n,
          true,
        );
      }
    }
  }

  return null;
}

function detectPair(
  rankCounts: Map<number, Card[]>,
  hasPhoenix: boolean,
  hasMahJong: boolean,
  cards: Card[],
): Combination | null {
  if (hasMahJong) return null;

  if (hasPhoenix) {
    if (rankCounts.size === 1) {
      const rank = rankCounts.keys().next().value!;
      return makeCombination("pair", cards, rank, 1);
    }
    return null;
  }

  if (rankCounts.size === 1) {
    const [rank, group] = rankCounts.entries().next().value!;
    if (group.length === 2) {
      return makeCombination("pair", cards, rank, 1);
    }
  }
  return null;
}

function detectTriple(
  rankCounts: Map<number, Card[]>,
  hasPhoenix: boolean,
  hasMahJong: boolean,
  cards: Card[],
): Combination | null {
  if (hasMahJong) return null;

  if (hasPhoenix) {
    if (rankCounts.size === 1) {
      const [rank, group] = rankCounts.entries().next().value!;
      if (group.length === 2) {
        return makeCombination("triple", cards, rank, 1);
      }
    }
    return null;
  }

  if (rankCounts.size === 1) {
    const [rank, group] = rankCounts.entries().next().value!;
    if (group.length === 3) {
      return makeCombination("triple", cards, rank, 1);
    }
  }
  return null;
}

function detectFullHouse(
  rankCounts: Map<number, Card[]>,
  hasPhoenix: boolean,
  hasMahJong: boolean,
  cards: Card[],
): Combination | null {
  if (hasMahJong) return null;

  const counts = new Map<number, number>();
  for (const [r, g] of rankCounts) counts.set(r, g.length);

  if (hasPhoenix) {
    if (counts.size === 2) {
      const sortedRanks = [...counts.keys()].sort((a, b) => a - b);
      const countVals = [...counts.values()].sort((a, b) => a - b);

      if (countVals[0] === 2 && countVals[1] === 2) {
        return makeCombination("full_house", cards, sortedRanks[1], 5);
      }
      if (countVals[0] === 1 && countVals[1] === 3) {
        const trioRank = [...counts.entries()].find(([, c]) => c === 3)![0];
        return makeCombination("full_house", cards, trioRank, 5);
      }
    }
  } else {
    if (counts.size === 2) {
      const countVals = [...counts.values()].sort((a, b) => a - b);
      if (countVals[0] === 2 && countVals[1] === 3) {
        const trioRank = [...counts.entries()].find(([, c]) => c === 3)![0];
        return makeCombination("full_house", cards, trioRank, 5);
      }
    }
  }
  return null;
}

function detectPairSequence(
  rankCounts: Map<number, Card[]>,
  hasPhoenix: boolean,
  hasMahJong: boolean,
  cards: Card[],
): Combination | null {
  if (hasMahJong) return null;

  const counts = new Map<number, number>();
  for (const [r, g] of rankCounts) counts.set(r, g.length);
  const sortedRanks = [...counts.keys()].sort((a, b) => a - b);

  if (sortedRanks.length === 0) return null;

  if (hasPhoenix) {
    const ones = [...counts.entries()]
      .filter(([, c]) => c === 1)
      .map(([r]) => r);
    if (ones.length !== 1) return null;
    if ([...counts.values()].some((c) => c > 2)) return null;
    const twos = [...counts.entries()]
      .filter(([, c]) => c === 2)
      .map(([r]) => r);
    const numPairs = twos.length + 1;
    if (numPairs < MIN_PAIR_SEQUENCE_PAIRS) return null;
    if (!isConsecutive(sortedRanks)) return null;
    return makeCombination(
      "pair_sequence",
      cards,
      sortedRanks[sortedRanks.length - 1],
      numPairs,
    );
  }

  if ([...counts.values()].some((c) => c !== 2)) return null;
  const numPairs = sortedRanks.length;
  if (numPairs < MIN_PAIR_SEQUENCE_PAIRS) return null;
  if (!isConsecutive(sortedRanks)) return null;

  return makeCombination(
    "pair_sequence",
    cards,
    sortedRanks[sortedRanks.length - 1],
    numPairs,
  );
}

function detectStraight(
  rankCounts: Map<number, Card[]>,
  hasPhoenix: boolean,
  hasMahJong: boolean,
  cards: Card[],
): Combination | null {
  const ranksInPlay: number[] = [];

  if (hasMahJong) ranksInPlay.push(1);

  for (const [rank, group] of rankCounts) {
    if (group.length !== 1) return null;
    ranksInPlay.push(rank);
  }

  ranksInPlay.sort((a, b) => a - b);

  if (hasPhoenix) {
    const result = fitPhoenixInStraight(ranksInPlay);
    if (result === null) return null;
    const [highRank, length] = result;
    if (length < MIN_STRAIGHT_LENGTH) return null;
    return makeCombination("straight", cards, highRank, length);
  }

  if (ranksInPlay.length < MIN_STRAIGHT_LENGTH) return null;
  if (!isConsecutive(ranksInPlay)) return null;

  return makeCombination(
    "straight",
    cards,
    ranksInPlay[ranksInPlay.length - 1],
    ranksInPlay.length,
  );
}

export function detectCombination(cards: Card[]): Combination | null {
  if (cards.length === 0) return null;
  if (cards.length === 1) return detectSingle(cards[0]);

  let phoenix: Card | null = null;
  const normalCards: Card[] = [];
  let hasDragon = false;
  let hasHound = false;

  for (const card of cards) {
    if (card.special === "phoenix") phoenix = card;
    else if (card.special === "dragon") hasDragon = true;
    else if (card.special === "hound") hasHound = true;
    else normalCards.push(card);
  }

  if (hasDragon || hasHound) return null;

  const bomb = detectBomb(cards, normalCards, phoenix !== null);
  if (bomb) return bomb;

  const mahJongCards = normalCards.filter((c) => c.special === "mah_jong");
  const rankableCards = normalCards.filter((c) => c.special !== "mah_jong");

  const rankCounts = new Map<number, Card[]>();
  for (const card of rankableCards) {
    const rank = card.rank!;
    const group = rankCounts.get(rank) ?? [];
    group.push(card);
    rankCounts.set(rank, group);
  }

  const hasPhoenix = phoenix !== null;
  const hasMahJong = mahJongCards.length > 0;
  const n = cards.length;

  if (n === 2) return detectPair(rankCounts, hasPhoenix, hasMahJong, cards);
  if (n === 3) return detectTriple(rankCounts, hasPhoenix, hasMahJong, cards);

  if (n === 5) {
    const fh = detectFullHouse(rankCounts, hasPhoenix, hasMahJong, cards);
    if (fh) return fh;
  }

  if (n >= 4 && n % 2 === 0) {
    const ps = detectPairSequence(rankCounts, hasPhoenix, hasMahJong, cards);
    if (ps) return ps;
  }

  if (n >= MIN_STRAIGHT_LENGTH) {
    const st = detectStraight(rankCounts, hasPhoenix, hasMahJong, cards);
    if (st) return st;
  }

  return null;
}

export function canPlayOn(
  play: Combination,
  currentTrick: Combination | null,
): boolean {
  if (currentTrick === null) return true;
  if (play.type === "hound_lead") return false;

  const isPhoenixSingle =
    play.type === "single" &&
    play.cards.length === 1 &&
    play.cards[0].special === "phoenix";
  const isDragonSingle =
    currentTrick.type === "single" &&
    currentTrick.cards.length === 1 &&
    currentTrick.cards[0].special === "dragon";
  if (isPhoenixSingle && isDragonSingle) return false;

  return combinationBeats(play, currentTrick);
}

function combinationBeats(a: Combination, b: Combination): boolean {
  if (a.is_bomb && !b.is_bomb) return true;
  if (!a.is_bomb && b.is_bomb) return false;
  if (a.is_bomb && b.is_bomb) {
    if (a.length !== b.length) return a.length > b.length;
    return a.rank > b.rank;
  }
  if (a.type !== b.type) return false;
  if (a.length !== b.length) return false;
  return a.rank > b.rank;
}
