import React, { useState, useEffect } from 'react';
import { notificationApi } from '../services/notificationApi';
import { NotificationPreferenceItem, NotificationType, NotificationChannel } from '../types/notification';

interface NotificationPreferencesPageProps {
  onNavigate?: (path: string) => void;
}

export const NotificationPreferencesPage: React.FC<NotificationPreferencesPageProps> = ({ onNavigate }) => {
  const [preferences, setPreferences] = useState<NotificationPreferenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchPrefs = async () => {
      try {
        const res = await notificationApi.getPreferences();
        setPreferences(res.preferences);
      } catch (err) {
        console.error('Failed to load preferences:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchPrefs();
  }, []);

  const togglePreference = (channel: NotificationChannel, type: NotificationType) => {
    setPreferences((prev) =>
      prev.map((p) =>
        p.channel === channel && p.notification_type === type
          ? { ...p, is_enabled: !p.is_enabled }
          : p
      )
    );
  };

  const handleSave = async () => {
    setSaving(true);
    setStatusMsg(null);
    try {
      await notificationApi.updatePreferences(preferences);
      setStatusMsg('Preferences successfully updated.');
    } catch {
      setStatusMsg('Failed to update preferences. Please retry.');
    } finally {
      setSaving(false);
    }
  };

  const categories: { type: NotificationType; label: string; desc: string }[] = [
    { type: 'DAILY_CHALLENGE', label: 'Daily Challenges', desc: 'Daily algorithmic challenge drops' },
    { type: 'STREAK_REMINDER', label: 'Streak Reminders', desc: 'Reminders before midnight to keep your solve streak' },
    { type: 'REVISION_DUE', label: 'Spaced Repetition', desc: 'Mistakes due for scheduled memory consolidation' },
    { type: 'CONTEST_STARTING', label: 'Live Contests', desc: 'Announcements 15 minutes before contests go live' },
    { type: 'ACHIEVEMENT_UNLOCKED', label: 'Achievements & Badges', desc: 'Rewards, badge milestones, and XP updates' },
    { type: 'SYSTEM_NOTICE', label: 'System Announcements', desc: 'Platform maintenance and feature notices' },
  ];

  return (
    <div className="min-h-screen bg-slate-950 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-5">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Notification Channels</h1>
            <p className="text-sm text-slate-400 mt-1">
              Select which alerts you want to receive in-app and via email.
            </p>
          </div>
          <button
            onClick={() => {
              if (onNavigate) {
                onNavigate('/notifications');
              } else {
                window.history.pushState({}, '', '/notifications');
              }
            }}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3.5 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer"
          >
            ← Back to Notifications
          </button>
        </div>

        {statusMsg && (
          <div className="rounded-lg bg-blue-900/40 border border-blue-500/30 p-3 text-xs text-blue-200">
            {statusMsg}
          </div>
        )}

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-xl">
          {loading ? (
            <div className="p-12 text-center text-sm text-slate-400">Loading settings...</div>
          ) : (
            <div className="divide-y divide-slate-800/60">
              <div className="grid grid-cols-12 bg-slate-900/80 px-6 py-3 text-xs font-semibold text-slate-400">
                <span className="col-span-8">NOTIFICATION EVENT</span>
                <span className="col-span-2 text-center">IN-APP</span>
                <span className="col-span-2 text-center">EMAIL</span>
              </div>

              {categories.map((cat) => {
                const inAppPref = preferences.find(
                  (p) => p.channel === 'IN_APP' && p.notification_type === cat.type
                );
                const emailPref = preferences.find(
                  (p) => p.channel === 'EMAIL' && p.notification_type === cat.type
                );

                return (
                  <div
                    key={cat.type}
                    className="grid grid-cols-12 items-center px-6 py-4 hover:bg-slate-800/20 transition-colors"
                  >
                    <div className="col-span-8 pr-4">
                      <p className="text-sm font-medium text-white">{cat.label}</p>
                      <p className="text-xs text-slate-400 mt-0.5">{cat.desc}</p>
                    </div>

                    <div className="col-span-2 flex justify-center">
                      <input
                        type="checkbox"
                        checked={inAppPref?.is_enabled ?? true}
                        onChange={() => togglePreference('IN_APP', cat.type)}
                        className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-blue-600 focus:ring-blue-500 cursor-pointer"
                        aria-label={`Enable in-app for ${cat.label}`}
                      />
                    </div>

                    <div className="col-span-2 flex justify-center">
                      <input
                        type="checkbox"
                        checked={emailPref?.is_enabled ?? true}
                        onChange={() => togglePreference('EMAIL', cat.type)}
                        className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-blue-600 focus:ring-blue-500 cursor-pointer"
                        aria-label={`Enable email for ${cat.label}`}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="border-t border-slate-800 bg-slate-900/80 px-6 py-4 flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving || loading}
              className="rounded-lg bg-blue-600 px-5 py-2 text-xs font-semibold text-white shadow hover:bg-blue-500 transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving Changes...' : 'Save Preferences'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
