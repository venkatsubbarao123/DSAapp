/**
 * Design system tokens exported as TypeScript constants for type-safe UI construction.
 */

export const themeTokens = {
  colors: {
    bgPrimary: "var(--bg-primary)",
    bgSecondary: "var(--bg-secondary)",
    bgTertiary: "var(--bg-tertiary)",
    bgCard: "var(--bg-card)",
    bgCardHover: "var(--bg-card-hover)",
    borderSubtle: "var(--border-subtle)",
    borderMuted: "var(--border-muted)",
    borderFocus: "var(--border-focus)",
    textPrimary: "var(--text-primary)",
    textSecondary: "var(--text-secondary)",
    textMuted: "var(--text-muted)",
    brandPrimary: "var(--brand-primary)",
    brandPrimaryHover: "var(--brand-primary-hover)",
    brandGlow: "var(--brand-glow)",
    statusSuccess: "var(--status-success)",
    statusWarning: "var(--status-warning)",
    statusDanger: "var(--status-danger)",
    statusInfo: "var(--status-info)",
  },
  spacing: {
    1: "var(--space-1)",
    2: "var(--space-2)",
    3: "var(--space-3)",
    4: "var(--space-4)",
    6: "var(--space-6)",
    8: "var(--space-8)",
    12: "var(--space-12)",
  },
  radii: {
    sm: "var(--radius-sm)",
    md: "var(--radius-md)",
    lg: "var(--radius-lg)",
    xl: "var(--radius-xl)",
    full: "var(--radius-full)",
  },
  breakpoints: {
    sm: "640px",
    md: "768px",
    lg: "1024px",
    xl: "1280px",
    "2xl": "1536px",
  },
} as const;
