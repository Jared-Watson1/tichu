import type { Card, GameState } from "../../types/game";
import { useWS } from "../../contexts/WebSocketContext";
import { detectCombination, canPlayOn } from "../../utils/combinationUtils";
import { WISH_RANKS, wishRankDisplay } from "../../utils/cardUtils";

interface ActionBarProps {
  gameState: GameState;
  selectedCards: Card[];
  onClearSelection: () => void;
}

export default function ActionBar({
  gameState,
  selectedCards,
  onClearSelection,
}: ActionBarProps) {
  const { actions } = useWS();
  const validActions = gameState.valid_actions;
  const currentTrickTop =
    gameState.trick.length > 0
      ? gameState.trick[gameState.trick.length - 1].combination
      : null;

  const selectedCombo =
    selectedCards.length > 0 ? detectCombination(selectedCards) : null;
  const canPlay =
    validActions.includes("play_cards") &&
    selectedCombo !== null &&
    canPlayOn(selectedCombo, currentTrickTop);

  const canPass = validActions.includes("pass");
  const canTichu = validActions.includes("call_small_tichu");
  const canBomb = validActions.includes("play_bomb");
  const needsWish =
    validActions.includes("make_wish") || validActions.includes("skip_wish");
  const needsDragonGive = validActions.includes("dragon_give");
  const needsGrandTichu = validActions.includes("grand_tichu_decision");
  const canStartNextRound = validActions.includes("start_game");

  const selectedBomb =
    canBomb && selectedCombo?.is_bomb ? selectedCombo : null;

  const handlePlay = () => {
    if (!canPlay) return;
    actions.playCards(selectedCards);
    onClearSelection();
  };

  const handleBomb = () => {
    if (!selectedBomb) return;
    actions.playBomb(selectedCards);
    onClearSelection();
  };

  const handlePass = () => {
    actions.passTurn();
    onClearSelection();
  };

  const yourSeat = gameState.your_seat;
  const leftOpp = (yourSeat + 1) % 4;
  const rightOpp = (yourSeat + 3) % 4;

  if (needsGrandTichu) {
    return (
      <div className="flex items-center justify-center gap-3 px-4 py-2">
        <button
          type="button"
          onClick={() => actions.grandTichuDecision(true)}
          className="px-5 py-2.5 rounded-lg bg-red-500 text-white font-bold
            hover:bg-red-400 transition-colors min-h-[44px]"
        >
          Grand Tichu!
        </button>
        <button
          type="button"
          onClick={() => actions.grandTichuDecision(false)}
          className="px-5 py-2.5 rounded-lg bg-gray-600 text-gray-200 font-semibold
            hover:bg-gray-500 transition-colors min-h-[44px]"
        >
          Pass
        </button>
      </div>
    );
  }

  if (needsWish) {
    return (
      <div className="flex flex-col items-center gap-2 px-4 py-2">
        <span className="text-amber-400 text-sm font-semibold">
          Make a wish (choose a rank)
        </span>
        <div className="flex flex-wrap justify-center gap-1.5">
          {WISH_RANKS.map((rank) => (
            <button
              key={rank}
              type="button"
              onClick={() => actions.makeWish(rank)}
              className="w-10 h-10 rounded-lg bg-gray-700 text-white text-sm font-bold
                hover:bg-amber-500 hover:text-gray-900 transition-colors"
            >
              {wishRankDisplay(rank)}
            </button>
          ))}
          <button
            type="button"
            onClick={() => actions.skipWish()}
            className="px-3 h-10 rounded-lg bg-gray-600 text-gray-300 text-sm
              hover:bg-gray-500 transition-colors"
          >
            No Wish
          </button>
        </div>
      </div>
    );
  }

  if (needsDragonGive) {
    return (
      <div className="flex flex-col items-center gap-2 px-4 py-2">
        <span className="text-amber-400 text-sm font-semibold">
          Give the dragon trick to an opponent
        </span>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => actions.dragonGive(leftOpp)}
            className="px-5 py-2.5 rounded-lg bg-gray-600 text-white font-semibold
              hover:bg-gray-500 transition-colors min-h-[44px]"
          >
            {gameState.players[leftOpp]?.name ?? `Seat ${leftOpp}`}
          </button>
          <button
            type="button"
            onClick={() => actions.dragonGive(rightOpp)}
            className="px-5 py-2.5 rounded-lg bg-gray-600 text-white font-semibold
              hover:bg-gray-500 transition-colors min-h-[44px]"
          >
            {gameState.players[rightOpp]?.name ?? `Seat ${rightOpp}`}
          </button>
        </div>
      </div>
    );
  }

  if (canStartNextRound) {
    return (
      <div className="flex items-center justify-center px-4 py-2">
        <button
          type="button"
          onClick={() => actions.startGame()}
          className="px-8 py-3 rounded-lg bg-amber-500 text-gray-900 font-bold text-lg
            hover:bg-amber-400 transition-colors min-h-[44px]"
        >
          {gameState.phase === "game_over" ? "New Game" : "Next Round"}
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center gap-3 px-4 py-2">
      <button
        type="button"
        onClick={handlePlay}
        disabled={!canPlay}
        className="px-5 py-2.5 rounded-lg bg-emerald-500 text-white font-bold
          hover:bg-emerald-400 disabled:opacity-30 disabled:cursor-not-allowed
          transition-colors min-h-[44px]"
      >
        Play
      </button>

      <button
        type="button"
        onClick={handlePass}
        disabled={!canPass}
        className="px-5 py-2.5 rounded-lg bg-gray-600 text-gray-200 font-semibold
          hover:bg-gray-500 disabled:opacity-30 disabled:cursor-not-allowed
          transition-colors min-h-[44px]"
      >
        Pass
      </button>

      {canTichu && (
        <button
          type="button"
          onClick={() => actions.callSmallTichu()}
          className="px-5 py-2.5 rounded-lg bg-amber-500 text-gray-900 font-bold
            hover:bg-amber-400 transition-colors min-h-[44px]"
        >
          Tichu!
        </button>
      )}

      {canBomb && (
        <button
          type="button"
          onClick={handleBomb}
          disabled={!selectedBomb}
          className="px-5 py-2.5 rounded-lg bg-red-500 text-white font-bold
            hover:bg-red-400 disabled:opacity-30 disabled:cursor-not-allowed
            transition-colors min-h-[44px]"
        >
          Bomb!
        </button>
      )}
    </div>
  );
}
