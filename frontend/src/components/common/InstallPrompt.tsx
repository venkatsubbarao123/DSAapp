import React, { useState } from 'react';
import { usePwa } from '../../pwa/registerSw';

export const InstallPrompt: React.FC = () => {
  const { isInstallable, triggerInstall } = usePwa();
  const [dismissed, setDismissed] = useState(false);

  if (!isInstallable || dismissed) {
    return null;
  }

  return (
    <div
      role="banner"
      aria-label="Install App"
      className="fixed bottom-4 right-4 z-50 flex items-center gap-3 rounded-xl border border-blue-500/30 bg-slate-900/95 p-4 text-white shadow-2xl backdrop-blur-md transition-all animate-in fade-in slide-in-from-bottom-5"
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-600 font-bold text-white shadow-md">
        DSA
      </div>
      <div>
        <h4 className="text-sm font-semibold">Install DSAapp</h4>
        <p className="text-xs text-slate-400">Offline practice, faster loads, full desktop experience</p>
      </div>
      <div className="flex items-center gap-2 ml-2">
        <button
          onClick={triggerInstall}
          className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white shadow hover:bg-blue-500 transition-colors"
        >
          Install
        </button>
        <button
          onClick={() => setDismissed(true)}
          className="rounded-lg border border-slate-700 px-2 py-1.5 text-xs text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          aria-label="Dismiss install prompt"
        >
          ✕
        </button>
      </div>
    </div>
  );
};
