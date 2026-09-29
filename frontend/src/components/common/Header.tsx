import React from "react";

interface HeaderProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  serviceHealthy?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentPath,
  onNavigate,
  serviceHealthy,
}) => {
  return (
    <header
      style={{
        borderBottom: "1px solid var(--border-subtle)",
        backgroundColor: "var(--bg-secondary)",
        padding: "0 var(--space-6)",
        height: "64px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-8)" }}>
        <button
          onClick={() => onNavigate("/")}
          style={{
            background: "none",
            border: "none",
            color: "var(--text-primary)",
            fontSize: "1.25rem",
            fontWeight: 700,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "var(--space-2)",
            padding: "var(--space-1) var(--space-2)",
            borderRadius: "var(--radius-sm)",
          }}
          aria-label="DSAapp Home"
        >
          <span
            style={{
              color: "var(--brand-primary)",
              backgroundColor: "var(--bg-tertiary)",
              padding: "2px 8px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-muted)",
              fontFamily: "var(--font-mono)",
            }}
          >
            DSA
          </span>
          <span>app</span>
        </button>

        <nav aria-label="Main Navigation">
          <ul
            style={{
              display: "flex",
              listStyle: "none",
              gap: "var(--space-2)",
            }}
          >
            <li>
              <button
                onClick={() => onNavigate("/")}
                style={{
                  background: currentPath === "/" ? "var(--bg-tertiary)" : "none",
                  border: "none",
                  color: currentPath === "/" ? "var(--text-primary)" : "var(--text-secondary)",
                  fontWeight: currentPath === "/" ? 600 : 400,
                  fontSize: "0.875rem",
                  padding: "var(--space-2) var(--space-4)",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                Overview
              </button>
            </li>
            <li>
              <button
                onClick={() => onNavigate("/status")}
                style={{
                  background: currentPath === "/status" ? "var(--bg-tertiary)" : "none",
                  border: "none",
                  color: currentPath === "/status" ? "var(--text-primary)" : "var(--text-secondary)",
                  fontWeight: currentPath === "/status" ? 600 : 400,
                  fontSize: "0.875rem",
                  padding: "var(--space-2) var(--space-4)",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                System Status
              </button>
            </li>
          </ul>
        </nav>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
        {serviceHealthy !== undefined && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-2)",
              fontSize: "0.75rem",
              padding: "4px 10px",
              borderRadius: "var(--radius-full)",
              backgroundColor: serviceHealthy ? "var(--status-success-bg)" : "var(--status-danger-bg)",
              color: serviceHealthy ? "var(--status-success)" : "var(--status-danger)",
              border: `1px solid ${serviceHealthy ? "var(--status-success)" : "var(--status-danger)"}`,
            }}
          >
            <span
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "var(--radius-full)",
                backgroundColor: "currentColor",
              }}
            />
            {serviceHealthy ? "API Online" : "API Offline"}
          </div>
        )}
        <span
          style={{
            fontSize: "0.75rem",
            color: "var(--text-muted)",
            fontFamily: "var(--font-mono)",
            border: "1px solid var(--border-subtle)",
            padding: "2px 8px",
            borderRadius: "var(--radius-sm)",
          }}
        >
          v0.1.0-phase1
        </span>
      </div>
    </header>
  );
};
