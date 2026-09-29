import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi';
import { AuditLogItem } from '../../types/admin';

export const AdminAuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Selected metadata modal
  const [activeMetadata, setActiveMetadata] = useState<{ id: string; json: string } | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await adminApi.listAuditLogs({
        page,
        pageSize: 30,
        action: actionFilter || undefined,
      });
      setLogs(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchLogs();
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Security & Admin Audit Trail</h1>
          <p className="text-xs text-slate-400 mt-1">
            Immutable, append-only log of role updates, privilege escalations, announcements, and critical actions.
          </p>
        </div>
        <span className="rounded-full bg-slate-900 border border-slate-800 px-3 py-1 text-xs text-slate-400">
          Recorded Events: <strong className="text-white">{total}</strong>
        </span>
      </div>

      {/* Filter Bar */}
      <form onSubmit={handleSearch} className="flex gap-3 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
        <input
          type="text"
          placeholder="Filter by action name (e.g. admin.update_role)..."
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-blue-500 transition-colors"
        >
          Search Logs
        </button>
      </form>

      {/* Audit Log Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
            <tr>
              <th className="px-4 py-3 font-semibold">Timestamp</th>
              <th className="px-4 py-3 font-semibold">Action</th>
              <th className="px-4 py-3 font-semibold">Actor ID</th>
              <th className="px-4 py-3 font-semibold">Target</th>
              <th className="px-4 py-3 font-semibold text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  Loading audit events...
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  No audit log entries found.
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 text-slate-400 whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 font-mono font-semibold text-blue-400">
                    {log.action}
                  </td>
                  <td className="px-4 py-3 font-mono text-[11px] text-slate-300">
                    {log.actor_id || 'system'}
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {log.target_type && (
                      <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400 mr-1.5">
                        {log.target_type}
                      </span>
                    )}
                    <span className="font-mono text-[11px] text-slate-400 truncate">
                      {log.target_id || '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {log.metadata_json ? (
                      <button
                        onClick={() => setActiveMetadata({ id: log.id, json: log.metadata_json || '{}' })}
                        className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 text-[11px] text-slate-300 hover:text-white transition-colors"
                      >
                        View JSON
                      </button>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* JSON Viewer Modal */}
      {activeMetadata && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="w-full max-w-lg rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">Event Context Metadata</h3>
              <button
                onClick={() => setActiveMetadata(null)}
                className="text-slate-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>
            <pre className="p-4 bg-slate-950 rounded-lg border border-slate-800 text-xs font-mono text-emerald-400 whitespace-pre-wrap overflow-x-auto max-h-72">
              {JSON.stringify(JSON.parse(activeMetadata.json), null, 2)}
            </pre>
            <div className="flex justify-end">
              <button
                onClick={() => setActiveMetadata(null)}
                className="rounded-lg bg-slate-800 px-4 py-1.5 text-xs text-white hover:bg-slate-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
