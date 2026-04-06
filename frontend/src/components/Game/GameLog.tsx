import { useEffect, useRef, useState } from "react";
import { useGameStore } from "../../stores/gameStore";

export default function GameLog() {
  const [open, setOpen] = useState(false);
  const log = useGameStore((s) => s.gameLog);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current && open) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [log, open]);

  return (
    <div className="absolute bottom-0 right-0 z-20">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="px-2 py-1 text-[10px] text-gray-400 bg-gray-800/80 border border-gray-700
          rounded-tl-lg hover:text-gray-200 transition-colors"
      >
        {open ? "Close Log" : "Log"}
        {!open && log.length > 0 && (
          <span className="ml-1 text-gray-500">({log.length})</span>
        )}
      </button>

      {open && (
        <div
          ref={scrollRef}
          className="w-64 max-h-48 overflow-y-auto bg-gray-900/95 border border-gray-700
            rounded-tl-lg p-2 text-[11px] text-gray-400 leading-relaxed"
        >
          {log.length === 0 ? (
            <div className="text-gray-600 italic">No events yet</div>
          ) : (
            log.map((entry, i) => (
              <div key={i} className="py-0.5 border-b border-gray-800 last:border-0">
                {entry}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
