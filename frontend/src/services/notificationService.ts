import { fetchPage, patchOne } from "../api/queryHelpers";
import type { Notification } from "../types/notification";

export const listNotifications = (params: { page?: number; page_size?: number } = {}) =>
  fetchPage<Notification>("/notifications", params);
export const markNotificationRead = (id: number) => patchOne<Notification>(`/notifications/${id}/read`);
export const markAllNotificationsRead = () => patchOne<{ updated: number }>("/notifications/read-all");
export const setDoNotDisturb = (dnd_enabled: boolean) =>
  patchOne<{ dnd_enabled: boolean }>("/notifications/dnd", { dnd_enabled });
