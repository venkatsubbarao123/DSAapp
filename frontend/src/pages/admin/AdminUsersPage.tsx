import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi';
import { AdminUserDetail, AdminUserListItem, UserRole } from '../../types/admin';

export const AdminUsersPage: React.FC = () => {
  const [users, setUsers] = useState<AdminUserListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [planFilter, setPlanFilter] = useState<string>('');
  const [loading, setLoading] = useState(true);

  // Selected user for modal
  const [selectedUser, setSelectedUser] = useState<AdminUserDetail | null>(null);
  const [actionReason, setActionReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await adminApi.listUsers({
        page,
        pageSize: 20,
        search: search || undefined,
        role: roleFilter ? (roleFilter as UserRole) : undefined,
        isActive: statusFilter === 'active' ? true : statusFilter === 'suspended' ? false : undefined,
        plan: planFilter || undefined,
      });
      setUsers(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [page, roleFilter, statusFilter, planFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchUsers();
  };

  const openUserDetail = async (userId: string) => {
    setModalError(null);
    setActionReason('');
    try {
      const detail = await adminApi.getUserDetail(userId);
      setSelectedUser(detail);
    } catch (err: any) {
      alert(err.message || 'Failed to fetch user details');
    }
  };

  const handleRoleChange = async (newRole: UserRole) => {
    if (!selectedUser) return;
    setActionLoading(true);
    setModalError(null);
    try {
      const updated = await adminApi.updateUserRole(selectedUser.id, {
        role: newRole,
        reason: actionReason || 'Admin console role mutation',
      });
      setSelectedUser(updated);
      fetchUsers();
    } catch (err: any) {
      setModalError(err.message || 'Role update rejected by server guardrails.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStatusToggle = async () => {
    if (!selectedUser) return;
    setActionLoading(true);
    setModalError(null);
    try {
      const updated = await adminApi.updateUserStatus(selectedUser.id, {
        is_active: !selectedUser.is_active,
        reason: actionReason || 'Admin console status mutation',
      });
      setSelectedUser(updated);
      fetchUsers();
    } catch (err: any) {
      setModalError(err.message || 'Status update rejected by server guardrails.');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Learner & User Directory</h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage student registrations, roles, premium plans, and administrative actions.
          </p>
        </div>
        <span className="rounded-full bg-slate-900 border border-slate-800 px-3 py-1 text-xs text-slate-400">
          Total Users: <strong className="text-white">{total}</strong>
        </span>
      </div>

      {/* Filter / Search Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
        <form onSubmit={handleSearchSubmit} className="sm:col-span-1">
          <input
            type="text"
            placeholder="Search email or name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </form>

        <select
          value={roleFilter}
          onChange={(e) => {
            setRoleFilter(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">All Roles</option>
          <option value="STUDENT">Student</option>
          <option value="CONTENT_EDITOR">Content Editor</option>
          <option value="MODERATOR">Moderator</option>
          <option value="ADMIN">Admin</option>
        </select>

        <select
          value={planFilter}
          onChange={(e) => {
            setPlanFilter(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">All Subscription Plans</option>
          <option value="FREE">Free</option>
          <option value="PREMIUM">Premium Pro</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">All Account Statuses</option>
          <option value="active">Active Only</option>
          <option value="suspended">Suspended Only</option>
        </select>
      </div>

      {/* Users Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
              <tr>
                <th className="px-4 py-3 font-semibold">User</th>
                <th className="px-4 py-3 font-semibold">Role</th>
                <th className="px-4 py-3 font-semibold">Plan</th>
                <th className="px-4 py-3 font-semibold">Status</th>
                <th className="px-4 py-3 font-semibold">Registered</th>
                <th className="px-4 py-3 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                    Loading users...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                    No users found matching query.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-white">{u.display_name}</div>
                      <div className="text-[11px] text-slate-400">{u.email}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-semibold text-slate-300">
                        {u.role}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                          u.plan === 'PREMIUM'
                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                            : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        {u.plan}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1.5 text-[11px] font-medium ${
                          u.is_active ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        <span
                          className={`h-1.5 w-1.5 rounded-full ${
                            u.is_active ? 'bg-emerald-400' : 'bg-rose-400'
                          }`}
                        />
                        {u.is_active ? 'Active' : 'Suspended'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-[11px]">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => openUserDetail(u.id)}
                        className="rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* User Detail & Mutation Modal */}
      {selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="w-full max-w-lg rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-white">Learner Profile Inspection</h2>
              <button
                onClick={() => setSelectedUser(null)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            {modalError && (
              <div className="rounded-lg bg-rose-950/40 border border-rose-500/30 p-3 text-xs text-rose-300">
                {modalError}
              </div>
            )}

            {/* Profile Overview */}
            <div className="grid grid-cols-2 gap-3 bg-slate-950/60 p-4 rounded-lg border border-slate-800 text-xs">
              <div>
                <span className="text-slate-500">Email:</span>
                <p className="font-semibold text-white truncate">{selectedUser.email}</p>
              </div>
              <div>
                <span className="text-slate-500">Display Name:</span>
                <p className="font-semibold text-white">{selectedUser.display_name}</p>
              </div>
              <div>
                <span className="text-slate-500">Solved Problems:</span>
                <p className="font-bold text-emerald-400">{selectedUser.solved_problems_count}</p>
              </div>
              <div>
                <span className="text-slate-500">Submissions Run:</span>
                <p className="font-bold text-blue-400">{selectedUser.submissions_count}</p>
              </div>
              <div>
                <span className="text-slate-500">Active Streak:</span>
                <p className="font-bold text-amber-400">{selectedUser.current_streak} days</p>
              </div>
              <div>
                <span className="text-slate-500">Total XP Earned:</span>
                <p className="font-bold text-purple-400">{selectedUser.total_xp} XP</p>
              </div>
            </div>

            {/* Role Mutation */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Update User Role</label>
              <div className="flex gap-2">
                {(['STUDENT', 'CONTENT_EDITOR', 'MODERATOR', 'ADMIN'] as UserRole[]).map((r) => (
                  <button
                    key={r}
                    disabled={actionLoading || selectedUser.role === r}
                    onClick={() => handleRoleChange(r)}
                    className={`rounded px-2.5 py-1.5 text-xs font-semibold transition-colors ${
                      selectedUser.role === r
                        ? 'bg-blue-600 text-white'
                        : 'border border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>

            {/* Action Reason */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">
                Audit Reason (Logged to Security Trail)
              </label>
              <input
                type="text"
                placeholder="Reason for role change or suspension..."
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Status Suspension Action */}
            <div className="flex items-center justify-between border-t border-slate-800 pt-4">
              <button
                disabled={actionLoading}
                onClick={handleStatusToggle}
                className={`rounded-lg px-4 py-2 text-xs font-semibold text-white transition-colors ${
                  selectedUser.is_active
                    ? 'bg-rose-600 hover:bg-rose-500'
                    : 'bg-emerald-600 hover:bg-emerald-500'
                }`}
              >
                {selectedUser.is_active ? 'Suspend Account' : 'Reactivate Account'}
              </button>

              <button
                onClick={() => setSelectedUser(null)}
                className="rounded-lg border border-slate-700 px-4 py-2 text-xs text-slate-300 hover:bg-slate-800"
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
