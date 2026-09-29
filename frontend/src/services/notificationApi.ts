/**
 * Notification API service client
 */

import { fetchApi } from './apiClient.ts';
import {
  AdminBroadcastRequest,
  AdminBroadcastResponse,
  NotificationItem,
  NotificationListResponse,
  NotificationPreferencesResponse,
  UnreadCountResponse,
  UpdatePreferenceItem,
} from '../types/notification.ts';

export const notificationApi = {
  async listNotifications(
    page: number = 1,
    pageSize: number = 20,
    unreadOnly: boolean = false
  ): Promise<NotificationListResponse> {
    const q = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      unread_only: unreadOnly ? 'true' : 'false',
    });
    const res = await fetchApi<NotificationListResponse>(`/api/v1/notifications?${q.toString()}`);
    return (res as any).data ?? res;
  },

  async getUnreadCount(): Promise<number> {
    const res = await fetchApi<UnreadCountResponse>('/api/v1/notifications/unread-count');
    const data = (res as any).data ?? res;
    return data.unread_count ?? 0;
  },

  async markAsRead(notificationId: string): Promise<NotificationItem> {
    const res = await fetchApi<NotificationItem>(`/api/v1/notifications/${notificationId}/read`, {
      method: 'PATCH',
    });
    return (res as any).data ?? res;
  },

  async markAllAsRead(): Promise<{ success: boolean; marked_count: number }> {
    const res = await fetchApi<{ success: boolean; marked_count: number }>('/api/v1/notifications/read-all', {
      method: 'POST',
    });
    return (res as any).data ?? res;
  },

  async getPreferences(): Promise<NotificationPreferencesResponse> {
    const res = await fetchApi<NotificationPreferencesResponse>('/api/v1/notifications/preferences');
    return (res as any).data ?? res;
  },

  async updatePreferences(preferences: UpdatePreferenceItem[]): Promise<NotificationPreferencesResponse> {
    const res = await fetchApi<NotificationPreferencesResponse>('/api/v1/notifications/preferences', {
      method: 'PUT',
      body: JSON.stringify({ preferences }),
    });
    return (res as any).data ?? res;
  },

  async broadcastNotification(payload: AdminBroadcastRequest): Promise<AdminBroadcastResponse> {
    const res = await fetchApi<AdminBroadcastResponse>('/api/v1/notifications/broadcast', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return (res as any).data ?? res;
  },
};
