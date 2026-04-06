export type Suit = "jade" | "sword" | "pagoda" | "star" | "special";

export type SpecialType = "dragon" | "phoenix" | "hound" | "mah_jong";

export interface Card {
  suit: Suit;
  rank: number | null;
  special: SpecialType | null;
}

export type CombinationType =
  | "single"
  | "pair"
  | "pair_sequence"
  | "triple"
  | "full_house"
  | "straight"
  | "four_bomb"
  | "straight_bomb"
  | "hound_lead";

export interface Combination {
  type: CombinationType;
  cards: Card[];
  rank: number;
  length: number;
  is_bomb: boolean;
}

export type GamePhase =
  | "waiting"
  | "dealing"
  | "grand_tichu"
  | "pushing"
  | "playing"
  | "round_over"
  | "game_over";

export interface PlayerPublicInfo {
  name: string;
  seat: number;
  team: number;
  card_count: number;
  has_gone_out: boolean;
  called_tichu: "small" | "grand" | null;
}

export interface TrickEntry {
  seat: number;
  combination: Combination;
}

export interface GameState {
  phase: GamePhase;
  your_hand: Card[];
  your_seat: number;
  players: PlayerPublicInfo[];
  current_player_seat: number;
  trick: TrickEntry[];
  active_wish: number | null;
  scores: [number, number];
  round_number: number;
  consecutive_passes: number;
  out_order: number[];
  can_play: boolean;
  valid_actions: string[];
}
