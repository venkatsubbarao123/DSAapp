import React, { useState } from 'react';
import { notificationApi } from '../../services/notificationApi';
import { NotificationChannel, NotificationType } from '../../types/notification';

export const AdminBroadcastPage: React.FC = () => {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [notifType, setNotifType] = useState<NotificationType>('SYSTEM_NOTICE');
  const [inApp, setInApp] = useState(true);
  const [email, setEmail] = useState(false);
  const [targetRole, setTargetRole] = useState('');
  const [targetPlan, setTargetPlan] = useState('');
  const [actionUrl, setActionUrl] = useState('');

  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<{ count: number; id: string } | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !body) return;

    const channels: NotificationChannel[] = [];
    if (inApp) channels.push('IN_APP');
    if (email) channels.push('EMAIL');

    if (channels.length === 0) {
      setErrorMsg('Please select at least one delivery channel (In-App or Email).');
      return;
    }

    setSending(true);
    setErrorMsg(null);
    setResult(null);

    try {
      const res = await notificationApi.broadcastNotification({
        title,
        body,
        type: notifType,
        channels,
        target_role: targetRole || undefined,
        target_plan: targetPlan || undefined,
        action_url: actionUrl || undefined,
      });

      setResult({
        count: res.dispatched_notifications,
        id: res.broadcast_id,
      });
      setTitle('');
      setBody('');
      setActionUrl('');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to dispatch broadcast.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-2xl font-bold text-white tracking-tight">Broadcast Announcements</h1>
        <p className="text-xs text-slate-400 mt-1">
          Dispatch multi-channel announcements to active students, with optional role and tier targeting.
        </p>
      </div>

      {result && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4 text-xs text-emerald-300">
          <h4 className="font-bold text-emerald-200">Broadcast Dispatched Successfully</h4>
          <p className="mt-1">
            Sent to <strong>{result.count}</strong> learner accounts. Broadcast Batch ID: <span className="font-mono text-[11px]">{result.id}</span>
          </p>
        </div>
      )}

      {errorMsg && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300">
          {errorMsg}
        </div>
      )}

      {/* Broadcast Form */}
      <form onSubmit={handleSubmit} className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl space-y-5">
        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-300">Announcement Title</label>
          <input
            type="text"
            placeholder="e.g. Weekly Contest #4 Goes Live in 1 Hour"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            required
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-300">Notification Message Body</label>
          <textarea
            rows={4}
            placeholder="Write clear educational guidance or platform announcement..."
            value={body}
            onChange={(e) => setBody(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            required
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Notification Type</label>
            <select
              value={notifType}
              onChange={(e) => setNotifType(e.target.value as NotificationType)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
            >
              <option value="SYSTEM_NOTICE">System Notice</option>
              <option value="CONTEST_STARTING">Contest Starting</option>
              <option value="DAILY_CHALLENGE">Daily Challenge</option>
              <option value="ACHIEVEMENT_UNLOCKED">Achievement Milestone</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Filter By Role</label>
            <select
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
            >
              <option value="">All Roles</option>
              <option value="STUDENT">Students Only</option>
              <option value="CONTENT_EDITOR">Content Editors Only</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Filter By Plan Tier</label>
            <select
              value={targetPlan}
              onChange={(e) => setTargetPlan(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
            >
              <option value="">All Plans</option>
              <option value="FREE">Free Tier Only</option>
              <option value="PREMIUM">Premium Pro Only</option>
            </select>
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-300">Optional Action URL (CTA)</label>
          <input
            type="text"
            placeholder="e.g. /contests or /practice"
            value={actionUrl}
            onChange={(e) => setActionUrl(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Delivery Channels */}
        <div className="space-y-2 border-t border-slate-800 pt-4">
          <label className="text-xs font-semibold text-slate-300 block">Dispatch Channels</label>
          <div className="flex items-center gap-6 text-xs">
            <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={inApp}
                onChange={(e) => setInApp(e.target.checked)}
                className="h-4 w-4 rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-blue-500"
              />
              <span>In-App Notification Drawer</span>
            </label>
            <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={email}
                onChange={(e) => setEmail(e.target.checked)}
                className="h-4 w-4 rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-blue-500"
              />
              <span>Email Delivery</span>
            </label>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={sending}
            className="rounded-lg bg-blue-600 px-6 py-2.5 text-xs font-semibold text-white shadow hover:bg-blue-500 transition-colors disabled:opacity-50"
          >
            {sending ? 'Dispatching Broadcast...' : 'Send Broadcast to Learners'}
          </button>
        </div>
      </form>
    </div>
  );
};
