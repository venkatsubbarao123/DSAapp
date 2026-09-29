import React from 'react';
import { usePwa } from '../../pwa/registerSw';

export const PwaUpdateToast: React.FC = () => {
  const { updateAvailable, applyUpdate } = usePwa();

  if (!updateAvailable) {
    return null;
  }

  return (
    <div
      role="alert"
      className="fixed top-4 right-4 z-50 flex items-center gap-3 rounded-xl border border-emerald-500/30 bg-slate-900/95 p-4 text-white shadow-2xl backdrop-blur-md animate-in fade-in slide-in-from-top-4"
    >
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-600/20 text-emerald-400">
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </div>
      <div>
        <h4 className="text-sm font-semibold text-white">App Update Available</h4>
        <p className="text-xs text-slate-400">A new version of DSAapp has been downloaded.</p>
      </div>
      <button
        onClick={applyUpdate}
        className="ml-2 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 transition-colors shadow"
      >
        Update Now
      </button>
    </div>
  );
};
