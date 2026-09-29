import React, { useState, useEffect } from 'react';
import { notificationApi } from '../services/notificationApi';
import { NotificationItem } from '../types/notification';

interface NotificationsPageProps {
  onNavigate?: (path: string) => void;
}

export const NotificationsPage: React.FC<NotificationsPageProps> = ({ onNavigate }) => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [page, setPage] = useState(1);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await notificationApi.listNotifications(page, 20, unreadOnly);
      setNotifications(res.items);
      setTotal(res.total);
      setUnreadCount(res.unread_count);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [page, unreadOnly]);

  const handleMarkAsRead = async (id: string) => {
    try {
      await notificationApi.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err) {
      console.error('Failed to mark read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationApi.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all read:', err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Notifications Center</h1>
            <p className="text-sm text-slate-400 mt-1">
              Stay updated on your daily challenges, streaks, contests, and achievements.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                if (onNavigate) {
                  onNavigate('/notifications/preferences');
                } else {
                  window.history.pushState({}, '', '/notifications/preferences');
                }
              }}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3.5 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer"
            >
              Channel Preferences
            </button>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white shadow hover:bg-blue-500 transition-colors"
              >
                Mark all as read
              </button>
            )}
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800/80 pb-3">
          <button
            onClick={() => {
              setUnreadOnly(false);
              setPage(1);
            }}
            className={`rounded-lg px-4 py-1.5 text-xs font-medium transition-colors ${
              !unreadOnly
                ? 'bg-blue-600 text-white shadow'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            All ({total})
          </button>
          <button
            onClick={() => {
              setUnreadOnly(true);
              setPage(1);
            }}
            className={`rounded-lg px-4 py-1.5 text-xs font-medium transition-colors ${
              unreadOnly
                ? 'bg-blue-600 text-white shadow'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            Unread ({unreadCount})
          </button>
        </div>

        {/* Notification List */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 divide-y divide-slate-800/60 overflow-hidden shadow-xl">
          {loading ? (
            <div className="p-12 text-center text-sm text-slate-400">Loading notifications...</div>
          ) : notifications.length === 0 ? (
            <div className="p-12 text-center text-sm text-slate-400">
              No notifications found matching your selection.
            </div>
          ) : (
            notifications.map((notif) => (
              <div
                key={notif.id}
                className={`p-5 transition-colors hover:bg-slate-800/30 flex items-start justify-between gap-4 ${
                  !notif.is_read ? 'bg-blue-950/20' : ''
                }`}
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-semibold text-slate-300">
                      {notif.type.replace(/_/g, ' ')}
                    </span>
                    {!notif.is_read && (
                      <span className="h-2 w-2 rounded-full bg-blue-500" title="Unread" />
                    )}
                    <span className="text-xs text-slate-400">
                      {new Date(notif.created_at).toLocaleString([], {
                        dateStyle: 'medium',
                        timeStyle: 'short',
                      })}
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-white">{notif.title}</h3>
                  <p className="text-xs text-slate-300 leading-relaxed">{notif.body}</p>
                </div>
                {!notif.is_read && (
                  <button
                    onClick={() => handleMarkAsRead(notif.id)}
                    className="shrink-0 rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
                  >
                    Mark read
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
