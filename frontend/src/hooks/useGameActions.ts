import { useCallback, useMemo } from "react";
import type { Card } from "../types/game";

type SendFn = (type: string, payload?: Record<string, unknown>) => void;

export function useGameActions(send: SendFn) {
  const createGame = useCallback(
    (playerName: string) => {
      send("create_game", { player_name: playerName });
    },
    [send],
  );

  const joinGame = useCallback(
    (gameId: string, playerName: string) => {
      send("join_game", { game_id: gameId, player_name: playerName });
    },
    [send],
  );

  const startGame = useCallback(() => {
    send("start_game");
  }, [send]);

  const grandTichuDecision = useCallback(
    (call: boolean) => {
      send("grand_tichu_decision", { call });
    },
    [send],
  );

  const pushCards = useCallback(
    (cardsMap: Record<number, Card>) => {
      const payload: Record<string, unknown> = {};
      for (const [seat, card] of Object.entries(cardsMap)) {
        payload[seat] = card;
      }
      send("push_cards", { cards: payload });
    },
    [send],
  );

  const playCards = useCallback(
    (cards: Card[]) => {
      send("play_cards", { cards });
    },
    [send],
  );

  const passTurn = useCallback(() => {
    send("pass_turn");
  }, [send]);

  const callSmallTichu = useCallback(() => {
    send("call_small_tichu");
  }, [send]);

  const makeWish = useCallback(
    (rank: number) => {
      send("make_wish", { rank });
    },
    [send],
  );

  const skipWish = useCallback(() => {
    send("skip_wish");
  }, [send]);

  const dragonGive = useCallback(
    (opponentSeat: number) => {
      send("dragon_give", { opponent_seat: opponentSeat });
    },
    [send],
  );

  const playBomb = useCallback(
    (cards: Card[]) => {
      send("play_bomb", { cards });
    },
    [send],
  );

  const addAiPlayer = useCallback(() => {
    send("add_ai_player");
  }, [send]);

  return useMemo(
    () => ({
      createGame,
      joinGame,
      startGame,
      grandTichuDecision,
      pushCards,
      playCards,
      passTurn,
      callSmallTichu,
      makeWish,
      skipWish,
      dragonGive,
      playBomb,
      addAiPlayer,
    }),
    [
      createGame,
      joinGame,
      startGame,
      grandTichuDecision,
      pushCards,
      playCards,
      passTurn,
      callSmallTichu,
      makeWish,
      skipWish,
      dragonGive,
      playBomb,
      addAiPlayer,
    ],
  );
}
