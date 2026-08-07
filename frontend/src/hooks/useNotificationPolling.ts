import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listNotifications } from "../services/notificationService";
import { useAuth } from "../context/AuthContext";
import type { Notification } from "../types/notification";

const POLL_INTERVAL_MS = 25_000;
const PAGE_SIZE = 20;

interface UseNotificationPollingResult {
  unreadCount: number;
  /** Newly-arrived unread notifications since the last poll — empty on the
   * very first load (nothing "arrived," it was just already there), so a
   * toast consumer never floods the screen with a user's entire backlog the
   * instant they open the app. Call `clearNewlyArrived()` once a consumer has
   * shown/queued these, so the same arrival isn't re-surfaced on every
   * subsequent render until the next real poll finds something new. */
  newlyArrived: Notification[];
  clearNewlyArrived: () => void;
}

/**
 * Single shared poll behind both the AppLayout unread badge and the toast
 * popup system, so two independent features don't each open their own
 * interval hitting the same endpoint. No dedicated backend endpoint exists
 * for "unread count" or "since timestamp" — this reuses the existing
 * GET /notifications list (already paginated/sorted newest-first) and
 * computes both derived values client-side.
 */
export function useNotificationPolling(): UseNotificationPollingResult {
  const { isAuthenticated } = useAuth();
  const seenIdsRef = useRef<Set<number> | null>(null);
  const [newlyArrived, setNewlyArrived] = useState<Notification[]>([]);

  const { data } = useQuery({
    queryKey: ["notifications", "poll"],
    queryFn: () => listNotifications({ page: 1, page_size: PAGE_SIZE }),
    enabled: isAuthenticated,
    refetchInterval: POLL_INTERVAL_MS,
    refetchIntervalInBackground: false,
  });

  useEffect(() => {
    const items = data?.items ?? [];
    if (items.length === 0) return;

    if (seenIdsRef.current === null) {
      // First load — record what's already there without treating any of it
      // as "new," so opening the app doesn't toast the whole backlog.
      seenIdsRef.current = new Set(items.map((n) => n.id));
      return;
    }

    const seen = seenIdsRef.current;
    const freshlyArrived = items.filter((n) => !n.read && !seen.has(n.id));
    for (const n of items) seen.add(n.id);

    if (freshlyArrived.length > 0) {
      setNewlyArrived((prev) => [...prev, ...freshlyArrived]);
    }
  }, [data]);

  const unreadCount = (data?.items ?? []).filter((n) => !n.read).length;

  const clearNewlyArrived = () => setNewlyArrived([]);

  return { unreadCount, newlyArrived, clearNewlyArrived };
}
