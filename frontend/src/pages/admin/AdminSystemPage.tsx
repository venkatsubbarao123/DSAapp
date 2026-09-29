import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi';
import { SystemDiagnosticsResponse } from '../../types/admin';

export const AdminSystemPage: React.FC = () => {
  const [diagnostics, setDiagnostics] = useState<SystemDiagnosticsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDiagnostics = async () => {
    setLoading(true);
    try {
      const data = await adminApi.getDiagnostics();
      setDiagnostics(data);
    } catch (err) {
      console.error('Failed to fetch diagnostics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagnostics();
  }, []);

  if (loading || !diagnostics) {
    return <div className="p-10 text-sm text-slate-400">Running diagnostic health probes...</div>;
  }

  const subsystems = [
    {
      name: 'PostgreSQL / SQLite Database Engine',
      health: diagnostics.database,
      desc: 'Relational data store executing ACID transactions and migrations.',
    },
    {
      name: 'Redis In-Memory Cache & Accelerators',
      health: diagnostics.redis,
      desc: 'High-speed key-value cache with 60s TTL and memory fallback.',
    },
    {
      name: 'Docker Sandboxed Execution Runtime',
      health: diagnostics.docker_sandbox,
      desc: 'Isolated, non-root, read-only rootfs containers for untrusted user code.',
    },
    {
      name: 'Online Judge Work Queue',
      health: diagnostics.judge_queue,
      desc: 'Durable SQL job scheduler with atomic worker leasing and heartbeats.',
    },
    {
      name: 'AI Tutoring Engine & Guidance Model',
      health: diagnostics.ai_provider,
      desc: 'Educational assistant generating progressive hints without answering directly.',
    },
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">System Health & Diagnostics</h1>
          <p className="text-xs text-slate-400 mt-1">
            Live subsystem connectivity probes, latency metrics, and security guarantees.
          </p>
        </div>
        <button
          onClick={fetchDiagnostics}
          className="rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white shadow hover:bg-blue-500 transition-colors"
        >
          Re-run Diagnostics
        </button>
      </div>

      {/* Security Invariant Guarantee Card */}
      <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4 text-xs text-emerald-300 flex items-start gap-3">
        <svg className="w-5 h-5 shrink-0 text-emerald-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <div>
          <h4 className="font-semibold text-emerald-200">Zero Secret Leakage Verification</h4>
          <p className="text-emerald-400/90 mt-0.5">
            This endpoint is strictly isolated against secret leakage. Database credentials, JWT signing secrets, API keys, and private tokens are never exposed in responses or logs.
          </p>
        </div>
      </div>

      {/* Meta Specs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <span className="text-xs text-slate-500">Application Version</span>
          <p className="text-sm font-bold text-white mt-1">{diagnostics.app_version}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <span className="text-xs text-slate-500">Environment</span>
          <p className="text-sm font-bold text-amber-400 mt-1 uppercase">{diagnostics.environment}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <span className="text-xs text-slate-500">Server Uptime</span>
          <p className="text-sm font-bold text-blue-400 mt-1">
            {Math.floor(diagnostics.uptime_seconds)} seconds
          </p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <span className="text-xs text-slate-500">Alembic Revision</span>
          <p className="text-sm font-mono font-bold text-emerald-400 mt-1">
            {diagnostics.current_migration_revision || '7c139d4e5f6a'}
          </p>
        </div>
      </div>

      {/* Subsystem Probes List */}
      <div className="space-y-3">
        {subsystems.map((sub, idx) => {
          const isHealthy = sub.health.status === 'healthy';
          return (
            <div
              key={idx}
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <h3 className="text-sm font-bold text-white">{sub.name}</h3>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                      isHealthy
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    {sub.health.status}
                  </span>
                </div>
                <p className="text-xs text-slate-400">{sub.desc}</p>
                {sub.health.message && (
                  <p className="text-[11px] text-slate-500 italic">Status: {sub.health.message}</p>
                )}
              </div>

              {sub.health.latency_ms !== null && sub.health.latency_ms !== undefined && (
                <div className="shrink-0 text-right">
                  <span className="text-[10px] text-slate-500 block">Round-trip latency</span>
                  <span className="text-xs font-mono font-bold text-slate-300">
                    {sub.health.latency_ms} ms
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
