import { createContext, useContext, type ReactNode } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { useGameActions } from "../hooks/useGameActions";

type SendFn = (type: string, payload?: Record<string, unknown>) => void;

interface WebSocketContextValue {
  send: SendFn;
  actions: ReturnType<typeof useGameActions>;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const { send } = useWebSocket();
  const actions = useGameActions(send);

  return (
    <WebSocketContext.Provider value={{ send, actions }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWS(): WebSocketContextValue {
  const ctx = useContext(WebSocketContext);
  if (!ctx) throw new Error("useWS must be used within WebSocketProvider");
  return ctx;
}
