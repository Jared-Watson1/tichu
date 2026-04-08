import type { Combination } from "./game";

export type ClientMsgType =
  | "create_game"
  | "join_game"
  | "start_game"
  | "grand_tichu_decision"
  | "push_cards"
  | "play_cards"
  | "pass_turn"
  | "call_small_tichu"
  | "make_wish"
  | "skip_wish"
  | "dragon_give"
  | "play_bomb"
  | "add_ai_player";

export type ServerMsgType =
  | "game_created"
  | "player_joined"
  | "game_starting"
  | "game_state"
  | "cards_played"
  | "player_passed"
  | "trick_won"
  | "tichu_called"
  | "wish_made"
  | "wish_fulfilled"
  | "player_out"
  | "round_over"
  | "game_over"
  | "error"
  | "player_disconnected"
  | "player_reconnected";

export interface ClientMessage {
  type: ClientMsgType;
  payload?: Record<string, unknown>;
}

export interface GameCreatedPayload {
  game_id: string;
  player_id: string;
  seat: number;
}

export interface PlayerJoinedPayload {
  player_id?: string;
  game_id?: string;
  player_name: string;
  seat: number;
  team: number;
  players?: Record<number, string>;
}

export interface CardsPlayedPayload {
  seat: number;
  combination: Combination;
}

export interface TichuCalledPayload {
  seat: number;
  tichu_type: "small" | "grand";
}

export interface WishMadePayload {
  rank: number;
}

export interface PlayerOutPayload {
  seat: number;
  position: number;
}

export interface RoundOverPayload {
  scores: [number, number];
  round_number: number;
}

export interface GameOverPayload {
  winning_team: number;
  final_scores: [number, number];
}

export interface ErrorPayload {
  message: string;
  code: string;
}

export interface PlayerDisconnectedPayload {
  seat: number;
}

export interface PlayerReconnectedPayload {
  seat: number;
  player_name: string;
}

export interface ServerMessage {
  type: ServerMsgType;
  payload: Record<string, unknown>;
}

export function createClientMessage(
  type: ClientMsgType,
  payload?: Record<string, unknown>,
): string {
  return JSON.stringify({ type, payload: payload ?? {} });
}
