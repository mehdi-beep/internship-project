import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Alert, Snackbar } from "@mui/material";
import { useNotificationPollingContext } from "../context/NotificationPollingContext";
import { categorizeNotification, type NotificationCategory } from "../utils/notificationCategory";
import { resolveNotificationPath } from "../utils/notificationRouting";
import { markNotificationRead } from "../services/notificationService";
import { useAuth } from "../context/AuthContext";
import type { Notification } from "../types/notification";

// MUI Alert only has 4 severities — "urgent" and "error" both read as red,
// which is the correct visual outcome (an urgent assignment IS an urgent,
// error-toned event), just mapped onto MUI's fixed vocabulary rather than a
// 5th custom color, since Snackbar/Alert don't support arbitrary severities.
const CATEGORY_TO_SEVERITY: Record<NotificationCategory, "error" | "success" | "info"> = {
  urgent: "error",
  error: "error",
  success: "success",
  info: "info",
};

/**
 * Mounted once, globally (see App.tsx) — shows newly-arrived unread
 * notifications as a dismissible toast, one at a time, in the order they
 * arrived. Purely additive: the Notifications page/inbox behavior is
 * completely unchanged, this is only an additional, transient surface for
 * catching something the instant it happens instead of only on the next
 * visit to /notifications.
 */
export default function NotificationToastQueue() {
  const { newlyArrived, clearNewlyArrived } = useNotificationPollingContext();
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [queue, setQueue] = useState<Notification[]>([]);
  const [current, setCurrent] = useState<Notification | null>(null);

  // Move newly-arrived items into the display queue, then immediately hand
  // them back to the poller as "handled" — the queue below is now the one
  // source of truth for what's still waiting to be shown.
  useEffect(() => {
    if (newlyArrived.length === 0) return;
    setQueue((prev) => [...prev, ...newlyArrived]);
    clearNewlyArrived();
  }, [newlyArrived, clearNewlyArrived]);

  useEffect(() => {
    if (current === null && queue.length > 0) {
      setCurrent(queue[0]);
      setQueue((prev) => prev.slice(1));
    }
  }, [current, queue]);

  const markReadMutation = useMutation({
    mutationFn: (notification: Notification) => markNotificationRead(notification.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  if (!current) return null;

  const handleClose = () => setCurrent(null);

  const handleClick = () => {
    const clicked = current;
    markReadMutation.mutate(clicked);
    if (user) {
      resolveNotificationPath(clicked, user.role).then((path) => {
        if (path) navigate(path);
      });
    }
    setCurrent(null);
  };

  return (
    <Snackbar
      open
      autoHideDuration={7000}
      onClose={handleClose}
      anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
    >
      <Alert
        onClose={handleClose}
        severity={CATEGORY_TO_SEVERITY[categorizeNotification(current)]}
        variant="filled"
        onClick={handleClick}
        sx={{ cursor: "pointer", minWidth: 320 }}
      >
        <strong>{current.title}</strong>
        <br />
        {current.message}
      </Alert>
    </Snackbar>
  );
}
