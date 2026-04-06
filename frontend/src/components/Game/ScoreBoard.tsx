import type { GameState } from "../../types/game";

interface ScoreBoardProps {
  gameState: GameState;
}

export default function ScoreBoard({ gameState }: ScoreBoardProps) {
  const [teamA, teamB] = gameState.scores;
  const players = gameState.players;
  const yourSeat = gameState.your_seat;
  const yourTeam = yourSeat % 2;

  const teamALabel = yourTeam === 0 ? "Your Team" : "Opponents";
  const teamBLabel = yourTeam === 1 ? "Your Team" : "Opponents";

  return (
    <div className="bg-gray-800/80 rounded-lg border border-gray-700 px-3 py-2 text-center">
      <div className="text-[10px] text-gray-500 mb-1">
        Round {gameState.round_number}
      </div>
      <div className="flex items-center gap-3 text-sm">
        <div className="flex flex-col items-center">
          <span className="text-[10px] text-gray-400">{teamALabel}</span>
          <span
            className={`font-bold text-lg ${teamA > teamB ? "text-emerald-400" : "text-gray-200"}`}
          >
            {teamA}
          </span>
        </div>
        <span className="text-gray-600">:</span>
        <div className="flex flex-col items-center">
          <span className="text-[10px] text-gray-400">{teamBLabel}</span>
          <span
            className={`font-bold text-lg ${teamB > teamA ? "text-emerald-400" : "text-gray-200"}`}
          >
            {teamB}
          </span>
        </div>
      </div>

      <div className="flex gap-2 mt-1 justify-center">
        {players.map((p) => {
          if (!p.called_tichu) return null;
          return (
            <span
              key={p.seat}
              className={`text-[9px] px-1 rounded
                ${p.called_tichu === "grand"
                  ? "bg-red-500/20 text-red-400"
                  : "bg-amber-500/20 text-amber-400"
                }`}
            >
              {p.name}: {p.called_tichu === "grand" ? "GT" : "T"}
            </span>
          );
        })}
      </div>
    </div>
  );
}
