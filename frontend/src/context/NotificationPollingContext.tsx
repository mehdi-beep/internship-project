import { createContext, useContext, type ReactNode } from "react";
import { useNotificationPolling } from "../hooks/useNotificationPolling";
import type { Notification } from "../types/notification";

interface NotificationPollingContextValue {
  unreadCount: number;
  newlyArrived: Notification[];
  clearNewlyArrived: () => void;
}

const NotificationPollingContext = createContext<NotificationPollingContextValue | undefined>(undefined);

/**
 * Wraps the single shared poll (see useNotificationPolling) in a Context so
 * the unread badge (AppLayout) and the toast popup queue consume the exact
 * same interval/state instead of each opening their own — mounted once in
 * App.tsx, same level as AuthProvider.
 */
export function NotificationPollingProvider({ children }: { children: ReactNode }) {
  const value = useNotificationPolling();
  return <NotificationPollingContext.Provider value={value}>{children}</NotificationPollingContext.Provider>;
}

export function useNotificationPollingContext(): NotificationPollingContextValue {
  const context = useContext(NotificationPollingContext);
  if (!context) {
    throw new Error("useNotificationPollingContext must be used within a NotificationPollingProvider");
  }
  return context;
}
