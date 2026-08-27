import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  List,
  ListItemButton,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import dayjs from "dayjs";
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "../services/notificationService";
import { resolveNotificationPath } from "../utils/notificationRouting";
import { useAuth } from "../context/AuthContext";
import type { Notification } from "../types/notification";

export default function NotificationsPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["notifications", page],
    queryFn: () => listNotifications({ page, page_size: 20 }),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["notifications"] });

  const markReadMutation = useMutation({
    mutationFn: (notification: Notification) => markNotificationRead(notification.id),
    onSuccess: invalidate,
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: invalidate,
  });

  const hasUnread = (data?.items ?? []).some((n) => !n.read);

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read) {
      markReadMutation.mutate(notification);
    }
    if (!user) return;
    const path = resolveNotificationPath(notification, user.role);
    if (path) {
      navigate(path);
    }
  };

  return (
    <Box>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          Notifications
        </Typography>
        <Button disabled={!hasUnread || markAllReadMutation.isPending} onClick={() => markAllReadMutation.mutate()}>
          Mark all as read
        </Button>
      </Stack>

      {isLoading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress />
        </Box>
      )}

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load notifications. Please check your connection and try again.
        </Alert>
      )}

      {!isLoading && !isError && (data?.items.length ?? 0) === 0 && (
        <Typography variant="body2" color="text.secondary">
          No notifications.
        </Typography>
      )}

      {!isLoading && !isError && (data?.items.length ?? 0) > 0 && (
        <List sx={{ bgcolor: "background.paper", borderRadius: 2 }}>
          {(data?.items ?? []).map((notification) => (
            <ListItemButton
              key={notification.id}
              onClick={() => handleNotificationClick(notification)}
              sx={{
                bgcolor: notification.read ? "transparent" : "action.hover",
                borderBottom: "1px solid",
                borderColor: "divider",
              }}
            >
              <ListItemText
                primary={
                  <Typography component="span" sx={{ fontWeight: notification.read ? 400 : 700 }}>
                    {notification.title}
                  </Typography>
                }
                secondary={
                  <>
                    {notification.message}
                    <br />
                    <Typography component="span" variant="caption" color="text.secondary">
                      {dayjs(notification.created_at).format("MMM D, YYYY HH:mm")}
                    </Typography>
                  </>
                }
              />
            </ListItemButton>
          ))}
        </List>
      )}

      {data && data.pages > 1 && (
        <Stack direction="row" spacing={1} sx={{ mt: 2, justifyContent: "center" }}>
          <Button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </Button>
          <Typography variant="body2" sx={{ alignSelf: "center" }}>
            Page {data.page} of {data.pages}
          </Typography>
          <Button disabled={page >= data.pages} onClick={() => setPage((p) => p + 1)}>
            Next
          </Button>
        </Stack>
      )}
    </Box>
  );
}
