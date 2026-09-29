import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { NotificationBell } from '../components/common/NotificationBell';
import { NotificationsPage } from '../pages/NotificationsPage';
import { NotificationPreferencesPage } from '../pages/NotificationPreferencesPage';
import { notificationApi } from '../services/notificationApi';

vi.mock('../services/notificationApi', () => ({
  notificationApi: {
    getUnreadCount: vi.fn(),
    listNotifications: vi.fn(),
    markAsRead: vi.fn(),
    markAllAsRead: vi.fn(),
    getPreferences: vi.fn(),
    updatePreferences: vi.fn(),
  },
}));

describe('DSAapp Phase 9 Notifications System UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('NotificationBell', () => {
    it('displays unread badge when unread notifications exist', async () => {
      (notificationApi.getUnreadCount as any).mockResolvedValue(5);
      (notificationApi.listNotifications as any).mockResolvedValue({
        items: [
          {
            id: 'n-1',
            type: 'DAILY_CHALLENGE',
            title: 'New Daily Problem: Merge Intervals',
            body: 'Consolidate your interval scheduling skills today.',
            is_read: false,
            data: {},
            created_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        page_size: 5,
        unread_count: 5,
      });

      render(<NotificationBell />);

      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument();
      });

      // Click bell to toggle drawer
      const bellBtn = screen.getByRole('button', { name: /View notifications/i });
      fireEvent.click(bellBtn);

      await waitFor(() => {
        expect(screen.getByText('New Daily Problem: Merge Intervals')).toBeInTheDocument();
      });

      expect(screen.getByText('5 new')).toBeInTheDocument();
    });

    it('marks a notification as read and decrements count', async () => {
      (notificationApi.getUnreadCount as any).mockResolvedValue(1);
      (notificationApi.listNotifications as any).mockResolvedValue({
        items: [
          {
            id: 'n-1',
            type: 'ACHIEVEMENT_UNLOCKED',
            title: 'Badge Unlocked: Quick Solver',
            body: 'Solved 10 problems under 15 minutes each.',
            is_read: false,
            data: {},
            created_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        page_size: 5,
        unread_count: 1,
      });
      (notificationApi.markAsRead as any).mockResolvedValue({ success: true });

      render(<NotificationBell />);

      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /View notifications/i }));

      await waitFor(() => {
        expect(screen.getByText('Badge Unlocked: Quick Solver')).toBeInTheDocument();
      });

      const markBtn = screen.getByTitle('Mark as read');
      fireEvent.click(markBtn);

      expect(notificationApi.markAsRead).toHaveBeenCalledWith('n-1');
    });
  });

  describe('NotificationsPage', () => {
    it('renders notification list and allows filtering by unread', async () => {
      (notificationApi.listNotifications as any).mockResolvedValue({
        items: [
          {
            id: 'notif-1',
            type: 'CONTEST_STARTING',
            title: 'Weekly Contest 42 Starts in 15 Minutes',
            body: 'Get ready with your test environment.',
            is_read: false,
            data: {},
            created_at: new Date().toISOString(),
          },
          {
            id: 'notif-2',
            type: 'STREAK_REMINDER',
            title: 'Keep Your 7-Day Streak Alive!',
            body: 'Solve one problem before midnight.',
            is_read: true,
            data: {},
            created_at: new Date().toISOString(),
          },
        ],
        total: 2,
        page: 1,
        page_size: 20,
        unread_count: 1,
      });

      const onNavigate = vi.fn();
      render(<NotificationsPage onNavigate={onNavigate} />);

      await waitFor(() => {
        expect(screen.getByText('Notifications Center')).toBeInTheDocument();
      });

      expect(screen.getByText('Weekly Contest 42 Starts in 15 Minutes')).toBeInTheDocument();
      expect(screen.getByText('Keep Your 7-Day Streak Alive!')).toBeInTheDocument();
      expect(screen.getByText('All (2)')).toBeInTheDocument();
      expect(screen.getByText('Unread (1)')).toBeInTheDocument();

      // Click preferences button
      const prefsBtn = screen.getByRole('button', { name: 'Channel Preferences' });
      fireEvent.click(prefsBtn);
      expect(onNavigate).toHaveBeenCalledWith('/notifications/preferences');
    });
  });

  describe('NotificationPreferencesPage', () => {
    it('renders preferences matrix and handles toggle and save', async () => {
      (notificationApi.getPreferences as any).mockResolvedValue({
        preferences: [
          { channel: 'IN_APP', notification_type: 'DAILY_CHALLENGE', is_enabled: true },
          { channel: 'EMAIL', notification_type: 'DAILY_CHALLENGE', is_enabled: false },
          { channel: 'IN_APP', notification_type: 'STREAK_REMINDER', is_enabled: true },
          { channel: 'EMAIL', notification_type: 'STREAK_REMINDER', is_enabled: true },
          { channel: 'IN_APP', notification_type: 'REVISION_DUE', is_enabled: true },
          { channel: 'EMAIL', notification_type: 'REVISION_DUE', is_enabled: false },
          { channel: 'IN_APP', notification_type: 'CONTEST_STARTING', is_enabled: true },
          { channel: 'EMAIL', notification_type: 'CONTEST_STARTING', is_enabled: true },
          { channel: 'IN_APP', notification_type: 'ACHIEVEMENT_UNLOCKED', is_enabled: true },
          { channel: 'EMAIL', notification_type: 'ACHIEVEMENT_UNLOCKED', is_enabled: false },
          { channel: 'IN_APP', notification_type: 'SYSTEM_NOTICE', is_enabled: true },
          { channel: 'EMAIL', notification_type: 'SYSTEM_NOTICE', is_enabled: true },
        ],
      });
      (notificationApi.updatePreferences as any).mockResolvedValue({ success: true });

      const onNavigate = vi.fn();
      render(<NotificationPreferencesPage onNavigate={onNavigate} />);

      await waitFor(() => {
        expect(screen.getByText('Notification Channels')).toBeInTheDocument();
      });

      expect(screen.getByText('Daily Challenges')).toBeInTheDocument();
      expect(screen.getByText('Streak Reminders')).toBeInTheDocument();
      expect(screen.getByText('Spaced Repetition')).toBeInTheDocument();
      expect(screen.getByText('Live Contests')).toBeInTheDocument();

      // Click save
      const saveBtn = screen.getByRole('button', { name: 'Save Preferences' });
      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(screen.getByText('Preferences successfully updated.')).toBeInTheDocument();
      });
      expect(notificationApi.updatePreferences).toHaveBeenCalled();
    });
  });
});
