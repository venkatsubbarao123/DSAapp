/**
 * Notification TypeScript interfaces and payloads
 */

export type NotificationType =
  | 'ACHIEVEMENT_UNLOCKED'
  | 'DAILY_CHALLENGE'
  | 'STREAK_REMINDER'
  | 'REVISION_DUE'
  | 'CONTEST_STARTING'
  | 'CONTEST_RESULT'
  | 'INTERVIEW_RESULT'
  | 'PREMIUM_EXPIRING'
  | 'SYSTEM_NOTICE';

export type NotificationChannel = 'IN_APP' | 'EMAIL';

export interface NotificationItem {
  id: string;
  user_id: string;
  type: NotificationType;
  title: string;
  body: string;
  data_json?: string | null;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  unread_count: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface NotificationPreferenceItem {
  channel: NotificationChannel;
  notification_type: NotificationType;
  is_enabled: boolean;
}

export interface NotificationPreferencesResponse {
  preferences: NotificationPreferenceItem[];
}

export interface UpdatePreferenceItem {
  channel: NotificationChannel;
  notification_type: NotificationType;
  is_enabled: boolean;
}

export interface UpdateNotificationPreferencesRequest {
  preferences: UpdatePreferenceItem[];
}

export interface AdminBroadcastRequest {
  title: string;
  body: string;
  type?: NotificationType;
  channels?: NotificationChannel[];
  target_role?: string;
  target_plan?: string;
  action_url?: string;
}

export interface AdminBroadcastResponse {
  success: boolean;
  recipient_count: number;
  dispatched_notifications: number;
  broadcast_id: string;
  channels: NotificationChannel[];
}
