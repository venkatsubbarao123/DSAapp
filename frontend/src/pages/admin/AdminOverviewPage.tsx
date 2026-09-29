import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi';
import { PlatformOverviewMetrics, SystemDiagnosticsResponse } from '../../types/admin';

interface AdminOverviewPageProps {
  onNavigate?: (path: string) => void;
}

export const AdminOverviewPage: React.FC<AdminOverviewPageProps> = ({ onNavigate }) => {
  const [metrics, setMetrics] = useState<PlatformOverviewMetrics | null>(null);
  const [diagnostics, setDiagnostics] = useState<SystemDiagnosticsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [m, d] = await Promise.all([
          adminApi.getPlatformOverview(),
          adminApi.getDiagnostics(),
        ]);
        setMetrics(m);
        setDiagnostics(d);
      } catch (err) {
        console.error('Failed to load admin overview:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <div className="p-10 text-sm text-slate-400">Loading platform overview...</div>;
  }

  const kpis = [
    { label: 'Total Users', value: (metrics?.total_users ?? 0).toLocaleString(), color: 'text-blue-400', sub: 'Registered accounts' },
    { label: 'Daily Active (DAU)', value: (metrics?.active_users_dau ?? 0).toLocaleString(), color: 'text-emerald-400', sub: '24h activity' },
    { label: 'Monthly Active (MAU)', value: (metrics?.active_users_mau ?? 0).toLocaleString(), color: 'text-cyan-400', sub: '30-day retention' },
    { label: 'Total Problems', value: (metrics?.total_problems ?? 0).toLocaleString(), color: 'text-amber-400', sub: 'Curriculum catalog' },
    { label: 'Total Submissions', value: (metrics?.total_submissions ?? 0).toLocaleString(), color: 'text-purple-400', sub: 'Evaluated code runs' },
    { label: 'Acceptance Rate', value: `${metrics?.platform_acceptance_rate ?? 0}%`, color: 'text-emerald-300', sub: `${(metrics?.total_accepted_submissions ?? 0).toLocaleString()} accepted` },
    { label: 'Pro Subscribers', value: (metrics?.total_premium_subscribers ?? 0).toLocaleString(), color: 'text-yellow-400', sub: 'Active recurring' },
    { label: 'Total Revenue', value: `₹${(metrics?.total_revenue_amount ?? 0).toLocaleString()}`, color: 'text-rose-400', sub: 'Verified completed' },
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Platform Command Center</h1>
          <p className="text-xs text-slate-400 mt-1">
            Authoritative platform KPIs, server diagnostics, and operational metrics.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              if (onNavigate) onNavigate('/admin/broadcast');
              else window.history.pushState({}, '', '/admin/broadcast');
            }}
            className="rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white shadow hover:bg-blue-500 transition-colors cursor-pointer border-0"
          >
            + Broadcast Announcement
          </button>
          <button
            onClick={() => {
              if (onNavigate) onNavigate('/admin/system');
              else window.history.pushState({}, '', '/admin/system');
            }}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-800 transition-colors cursor-pointer"
          >
            System Diagnostics
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {kpis.map((kpi, idx) => (
          <div
            key={idx}
            className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 shadow-lg flex flex-col justify-between"
          >
            <span className="text-xs font-medium text-slate-400">{kpi.label}</span>
            <div className="my-2">
              <span className={`text-2xl font-black ${kpi.color}`}>{kpi.value}</span>
            </div>
            <span className="text-[11px] text-slate-500">{kpi.sub}</span>
          </div>
        ))}
      </div>

      {/* Subsystems Snapshot */}
      {diagnostics && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-sm font-semibold text-white">Live Subsystems Health Status</h2>
            <span className="text-xs text-slate-400">
              Server Uptime: {Math.floor(diagnostics.uptime_seconds / 60)} min
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
            {[
              { name: 'Database', health: diagnostics.database },
              { name: 'Redis Cache', health: diagnostics.redis },
              { name: 'Docker Sandbox', health: diagnostics.docker_sandbox },
              { name: 'Judge Queue', health: diagnostics.judge_queue },
              { name: 'AI Tutor', health: diagnostics.ai_provider },
            ].map((sub, idx) => {
              const isHealthy = sub.health.status === 'healthy';
              return (
                <div
                  key={idx}
                  className="rounded-lg border border-slate-800/80 bg-slate-950/60 p-3 flex flex-col justify-between"
                >
                  <span className="text-xs font-medium text-slate-300">{sub.name}</span>
                  <div className="flex items-center gap-2 mt-2">
                    <span
                      className={`h-2.5 w-2.5 rounded-full ${
                        isHealthy ? 'bg-emerald-500' : 'bg-amber-500'
                      }`}
                    />
                    <span className="text-xs font-semibold uppercase tracking-wider text-white">
                      {sub.health.status}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 mt-1 truncate">
                    {sub.health.message || 'Operational'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          onClick={() => {
            if (onNavigate) onNavigate('/admin/users');
            else window.history.pushState({}, '', '/admin/users');
          }}
          className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 hover:bg-slate-900/80 transition-all shadow hover:border-slate-700 block cursor-pointer"
        >
          <h3 className="text-sm font-semibold text-white">User Management</h3>
          <p className="text-xs text-slate-400 mt-1">
            Search users, review profile metrics, elevate editorial roles, and handle account status.
          </p>
        </div>
        <div
          onClick={() => {
            if (onNavigate) onNavigate('/admin/problems');
            else window.history.pushState({}, '', '/admin/problems');
          }}
          className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 hover:bg-slate-900/80 transition-all shadow hover:border-slate-700 block cursor-pointer"
        >
          <h3 className="text-sm font-semibold text-white">Problem & Test Case Studio</h3>
          <p className="text-xs text-slate-400 mt-1">
            Configure algorithmic problems and author hidden test cases for secure online judging.
          </p>
        </div>
        <div
          onClick={() => {
            if (onNavigate) onNavigate('/admin/audit');
            else window.history.pushState({}, '', '/admin/audit');
          }}
          className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 hover:bg-slate-900/80 transition-all shadow hover:border-slate-700 block cursor-pointer"
        >
          <h3 className="text-sm font-semibold text-white">Security Audit Log</h3>
          <p className="text-xs text-slate-400 mt-1">
            Inspect immutable audit trails for administrative role updates, logins, and broadcasts.
          </p>
        </div>
      </div>
    </div>
  );
};
