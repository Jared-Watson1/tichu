import { useState } from "react";
import { useGameStore } from "../../stores/gameStore";
import type { Card } from "../../types/game";
import PlayerHand from "./PlayerHand";
import OpponentHand from "./OpponentHand";
import TrickArea from "./TrickArea";
import ActionBar from "./ActionBar";
import CardPush from "./CardPush";
import WishIndicator from "./WishIndicator";
import ScoreBoard from "./ScoreBoard";
import GameLog from "./GameLog";
import TurnIndicator from "./TurnIndicator";

export default function GameBoard() {
  const gameState = useGameStore((s) => s.gameState);
  const lastTrickWinner = useGameStore((s) => s.lastTrickWinner);
  const connectionStatus = useGameStore((s) => s.connectionStatus);
  const [selectedCards, setSelectedCards] = useState<Card[]>([]);

  if (!gameState) {
    return (
      <div className="h-screen flex items-center justify-center text-gray-400">
        Waiting for game state...
      </div>
    );
  }

  const yourSeat = gameState.your_seat;
  const partner = (yourSeat + 2) % 4;
  const leftOpp = (yourSeat + 1) % 4;
  const rightOpp = (yourSeat + 3) % 4;

  const isPlaying = gameState.phase === "playing";
  const isPushing = gameState.phase === "pushing";
  const isGrandTichu = gameState.phase === "grand_tichu";
  const isRoundOver = gameState.phase === "round_over";
  const isGameOver = gameState.phase === "game_over";
  const isYourTurn = gameState.can_play;

  const clearSelection = () => setSelectedCards([]);

  const playerNames = gameState.players.map((p) => p.name);

  return (
    <div className="h-screen bg-gray-900 flex flex-col overflow-hidden relative">
      {/* Connection status overlay */}
      {connectionStatus === "disconnected" && (
        <div className="absolute inset-0 z-50 bg-black/60 flex items-center justify-center">
          <div className="bg-gray-800 border border-red-500/50 rounded-xl px-6 py-4 text-center">
            <div className="text-red-400 font-bold mb-1">Disconnected</div>
            <div className="text-gray-400 text-sm">Reconnecting...</div>
          </div>
        </div>
      )}

      {/* Top row: partner hand + scoreboard */}
      <div className="flex items-start justify-between px-4 pt-2 shrink-0" style={{ minHeight: "15%" }}>
        <div className="flex-1 flex justify-center">
          <OpponentHand
            player={gameState.players[partner]}
            position="top"
            isCurrentTurn={isPlaying && gameState.current_player_seat === partner}
            isTeammate
            outOrder={gameState.out_order}
          />
        </div>
        <ScoreBoard gameState={gameState} />
      </div>

      {/* Middle row: left opp + trick area + right opp */}
      <div className="flex-1 flex items-center min-h-0">
        <div className="w-28 shrink-0 flex justify-center">
          <OpponentHand
            player={gameState.players[leftOpp]}
            position="left"
            isCurrentTurn={isPlaying && gameState.current_player_seat === leftOpp}
            outOrder={gameState.out_order}
          />
        </div>

        <div className="flex-1 relative h-full">
          {isPlaying && (
            <>
              <TrickArea
                trick={gameState.trick}
                yourSeat={yourSeat}
                lastTrickWinner={lastTrickWinner}
              />
              <WishIndicator activeWish={gameState.active_wish} />
              <TurnIndicator
                currentPlayerSeat={gameState.current_player_seat}
                yourSeat={yourSeat}
                playerNames={playerNames}
              />
            </>
          )}

          {isRoundOver && (
            <div className="w-full h-full flex flex-col items-center justify-center gap-2">
              <div className="text-xl font-bold text-white">Round Over</div>
              <div className="text-gray-300">
                Score: {gameState.scores[0]} - {gameState.scores[1]}
              </div>
            </div>
          )}

          {isGameOver && (
            <div className="w-full h-full flex flex-col items-center justify-center gap-2">
              <div className="text-2xl font-bold text-amber-400">Game Over</div>
              <div className="text-gray-300 text-lg">
                {gameState.scores[0]} - {gameState.scores[1]}
              </div>
              <div className="text-emerald-400 font-semibold">
                {gameState.scores[0] > gameState.scores[1]
                  ? yourSeat % 2 === 0
                    ? "Your team wins!"
                    : "Opponents win"
                  : yourSeat % 2 === 1
                    ? "Your team wins!"
                    : "Opponents win"}
              </div>
            </div>
          )}

          {isGrandTichu && (
            <div className="w-full h-full flex items-center justify-center">
              <div className="text-amber-400 text-lg font-semibold">
                Grand Tichu Decision
              </div>
            </div>
          )}

          {isPushing && (
            <div className="w-full h-full flex items-center justify-center p-4">
              <div className="text-amber-400 text-sm">
                Select cards to push to each player
              </div>
            </div>
          )}
        </div>

        <div className="w-28 shrink-0 flex justify-center">
          <OpponentHand
            player={gameState.players[rightOpp]}
            position="right"
            isCurrentTurn={isPlaying && gameState.current_player_seat === rightOpp}
            outOrder={gameState.out_order}
          />
        </div>
      </div>

      {/* Bottom row: action bar + player hand */}
      <div
        className={`shrink-0 pb-2 transition-shadow duration-300
          ${isYourTurn ? "shadow-[0_-4px_20px_rgba(16,185,129,0.15)]" : ""}`}
      >
        {isPushing ? (
          <CardPush hand={gameState.your_hand} />
        ) : (
          <>
            <ActionBar
              gameState={gameState}
              selectedCards={selectedCards}
              onClearSelection={clearSelection}
            />
            <PlayerHand
              cards={gameState.your_hand}
              selectedCards={selectedCards}
              onSelectionChange={setSelectedCards}
              disabled={
                !isPlaying && !isGrandTichu
              }
            />
          </>
        )}
      </div>

      <GameLog />
    </div>
  );
}
