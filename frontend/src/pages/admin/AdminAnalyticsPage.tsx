import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi';
import { ComprehensiveAnalyticsResponse } from '../../types/admin';

export const AdminAnalyticsPage: React.FC = () => {
  const [analytics, setAnalytics] = useState<ComprehensiveAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAnalytics = async (force: boolean = false) => {
    if (force) setRefreshing(true);
    else setLoading(true);

    try {
      const data = await adminApi.getComprehensiveAnalytics(force);
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading || !analytics) {
    return <div className="p-10 text-sm text-slate-400">Loading comprehensive analytics...</div>;
  }

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Platform Analytics & Insights</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time multi-domain analytics with 60-second Redis caching and database aggregations.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`rounded-full px-2.5 py-1 text-[11px] font-semibold border ${
              analytics.cached
                ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
            }`}
          >
            {analytics.cached ? 'Redis Cached (60s TTL)' : 'Live Database Aggregation'}
          </span>
          <button
            onClick={() => fetchAnalytics(true)}
            disabled={refreshing}
            className="rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white shadow hover:bg-blue-500 transition-colors disabled:opacity-50"
          >
            {refreshing ? 'Refreshing...' : 'Bypass Cache & Refresh'}
          </button>
        </div>
      </div>

      {/* Grid of Domain Analytics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* User Acquisition & Retention */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xl space-y-4">
          <h2 className="text-sm font-semibold text-white border-b border-slate-800 pb-2">
            User Demographics & Subscriptions
          </h2>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400">Total Accounts</span>
              <p className="text-xl font-bold text-white mt-1">{analytics.users.total_users}</p>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400">Active vs Suspended</span>
              <p className="text-xl font-bold text-emerald-400 mt-1">
                {analytics.users.active_users}{' '}
                <span className="text-xs text-rose-400 font-normal">/ {analytics.users.suspended_users} susp.</span>
              </p>
            </div>
          </div>

          <div className="space-y-2 pt-2">
            <span className="text-xs font-semibold text-slate-300">Role Breakdown</span>
            <div className="space-y-1.5">
              {analytics.users.role_distribution.map((r) => (
                <div key={r.category} className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">{r.category}</span>
                  <span className="font-semibold text-white">
                    {r.count} ({r.percentage}%)
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Online Judge Performance */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xl space-y-4">
          <h2 className="text-sm font-semibold text-white border-b border-slate-800 pb-2">
            Online Judge Operations & Runtime
          </h2>
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400">Queue Depth</span>
              <p className="text-xl font-bold text-blue-400 mt-1">{analytics.judge.queue_depth}</p>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400">Running Workers</span>
              <p className="text-xl font-bold text-amber-400 mt-1">{analytics.judge.running_jobs}</p>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400">Total Jobs</span>
              <p className="text-xl font-bold text-emerald-400 mt-1">{analytics.judge.total_jobs_executed}</p>
            </div>
          </div>

          <div className="space-y-2 pt-2">
            <span className="text-xs font-semibold text-slate-300">Submission Verdicts</span>
            <div className="grid grid-cols-2 gap-2">
              {analytics.judge.verdict_breakdown.map((v) => (
                <div
                  key={v.category}
                  className="rounded bg-slate-950/40 border border-slate-800/80 p-2 flex items-center justify-between text-xs"
                >
                  <span className="text-slate-400 text-[11px] truncate">{v.category}</span>
                  <span className="font-bold text-white">{v.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Gamification & Streaks */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xl space-y-4">
          <h2 className="text-sm font-semibold text-white border-b border-slate-800 pb-2">
            Gamification & Habit Formation
          </h2>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400">XP Issued</span>
              <p className="text-xl font-bold text-purple-400 mt-1">
                {analytics.gamification.total_xp_distributed.toLocaleString()}
              </p>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400">Active Streaks</span>
              <p className="text-xl font-bold text-amber-400 mt-1">
                {analytics.gamification.users_with_active_streaks} learners
              </p>
            </div>
          </div>

          <div className="space-y-2 pt-2">
            <span className="text-xs font-semibold text-slate-300">Streak Tiers</span>
            <div className="space-y-1.5">
              {analytics.gamification.streak_tier_distribution.map((t) => (
                <div key={t.category} className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">{t.category}</span>
                  <span className="font-semibold text-white">{t.count} users</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Contests & Interviews */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xl space-y-4">
          <h2 className="text-sm font-semibold text-white border-b border-slate-800 pb-2">
            Competitive & Interview Modes
          </h2>
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400">Contests</span>
              <p className="text-xl font-bold text-white mt-1">{analytics.competition.total_contests}</p>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400">Registrations</span>
              <p className="text-xl font-bold text-cyan-400 mt-1">
                {analytics.competition.total_contest_registrations}
              </p>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400">Interviews</span>
              <p className="text-xl font-bold text-emerald-400 mt-1">
                {analytics.competition.total_mock_interviews}
              </p>
            </div>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800 text-xs flex justify-between items-center">
            <span className="text-slate-400">Average Interview Score:</span>
            <span className="text-sm font-bold text-white">
              {analytics.competition.average_interview_score} / 100
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
