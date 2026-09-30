import React, { useState, useRef, useEffect } from 'react';
import { useTheme, Theme } from '../../context/ThemeContext.tsx';

const THEME_OPTIONS: { value: Theme; label: string; icon: string }[] = [
  { value: 'light', label: 'Light', icon: '☀️' },
  { value: 'dark', label: 'Dark', icon: '🌙' },
  { value: 'system', label: 'System', icon: '💻' },
];

function getCurrentIcon(theme: Theme, resolvedTheme: 'light' | 'dark'): string {
  if (theme === 'system') return '💻';
  return resolvedTheme === 'dark' ? '🌙' : '☀️';
}

export const ThemeToggle: React.FC = () => {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close on outside click or Escape
  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('keydown', handleKey);
    document.addEventListener('mousedown', handleClick);
    return () => {
      document.removeEventListener('keydown', handleKey);
      document.removeEventListener('mousedown', handleClick);
    };
  }, [open]);

  const handleSelect = (t: Theme) => {
    setTheme(t);
    setOpen(false);
  };

  return (
    <div ref={containerRef} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={`Theme: ${theme}. Click to change.`}
        aria-expanded={open}
        aria-haspopup="listbox"
        style={{
          background: 'none',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--text-secondary)',
          cursor: 'pointer',
          padding: '6px 10px',
          fontSize: '1rem',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          transition: 'border-color 0.15s ease',
        }}
        onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-muted)'; }}
        onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-subtle)'; }}
      >
        <span role="img" aria-hidden="true">{getCurrentIcon(theme, resolvedTheme)}</span>
      </button>

      {open && (
        <div
          role="listbox"
          aria-label="Theme selection"
          style={{
            position: 'absolute',
            top: 'calc(100% + 8px)',
            right: 0,
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            boxShadow: 'var(--shadow-lg)',
            zIndex: 100,
            minWidth: '140px',
            overflow: 'hidden',
          }}
        >
          {THEME_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              role="option"
              aria-selected={theme === opt.value}
              onClick={() => handleSelect(opt.value)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-2)',
                width: '100%',
                padding: 'var(--space-2) var(--space-4)',
                background: theme === opt.value ? 'var(--bg-tertiary)' : 'none',
                border: 'none',
                color: theme === opt.value ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontWeight: theme === opt.value ? 600 : 400,
                fontSize: '0.875rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'background 0.1s ease',
              }}
              onMouseEnter={(e) => {
                if (theme !== opt.value) {
                  (e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-tertiary)';
                }
              }}
              onMouseLeave={(e) => {
                if (theme !== opt.value) {
                  (e.currentTarget as HTMLButtonElement).style.background = 'none';
                }
              }}
            >
              <span role="img" aria-hidden="true">{opt.icon}</span>
              {opt.label}
              {theme === opt.value && (
                <span style={{ marginLeft: 'auto', color: 'var(--brand-primary)' }}>✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
