import React from 'react';
import { useAuth } from '../../context/AuthContext';

export interface AdminLayoutProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  children: React.ReactNode;
}

export const AdminLayout: React.FC<AdminLayoutProps> = ({ currentPath, onNavigate, children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-400">
        Loading administration portal...
      </div>
    );
  }

  // Admin access gate: Only ADMIN role is authorized
  if (!isAuthenticated || user?.role !== 'ADMIN') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-100 p-6">
        <div className="max-w-md w-full text-center p-8 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl">
          <div className="w-12 h-12 rounded-full bg-red-900/30 text-red-500 mx-auto flex items-center justify-center font-bold text-xl mb-4 border border-red-500/20">
            !
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Access Denied</h2>
          <p className="text-sm text-slate-400 mb-6">
            Administrator privileges (Role: ADMIN) are required to access this portal.
          </p>
          <button
            onClick={() => onNavigate('/')}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-semibold transition-colors cursor-pointer"
          >
            Return to Platform Home
          </button>
        </div>
      </div>
    );
  }

  const navItems = [
    { label: 'Overview', to: '/admin', end: true },
    { label: 'Learners & Users', to: '/admin/users' },
    { label: 'Problems & Tests', to: '/admin/problems' },
    { label: 'Platform Analytics', to: '/admin/analytics' },
    { label: 'System Diagnostics', to: '/admin/system' },
    { label: 'Security Audit Logs', to: '/admin/audit' },
    { label: 'Broadcast Alerts', to: '/admin/broadcast' },
  ];

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 border-r border-slate-800 bg-slate-900/70 p-5 backdrop-blur-md hidden md:flex md:flex-col justify-between">
        <div className="space-y-6">
          <div className="flex items-center gap-3 px-2 cursor-pointer" onClick={() => onNavigate('/admin')}>
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 font-black text-white shadow-lg">
              ADM
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-wide">DSAapp Admin</h2>
              <span className="text-[10px] uppercase tracking-wider text-blue-400 font-semibold">
                Superuser Console
              </span>
            </div>
          </div>

          <nav className="space-y-1">
            {navItems.map((item) => {
              const isActive = item.end ? currentPath === item.to : currentPath.startsWith(item.to);
              return (
                <button
                  key={item.to}
                  onClick={() => onNavigate(item.to)}
                  className={`w-full text-left flex items-center gap-3 rounded-lg px-3 py-2.5 text-xs font-semibold transition-all border-0 cursor-pointer ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-transparent text-slate-400 hover:bg-slate-800 hover:text-slate-100'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-3 text-[11px] text-slate-400">
          <p className="font-semibold text-slate-300">Phase 9 Console</p>
          <p className="text-[10px] text-slate-500 mt-0.5">Real-time DB analytics & Docker monitor</p>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
};
