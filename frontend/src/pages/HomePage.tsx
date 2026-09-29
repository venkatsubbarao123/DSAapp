import React from "react";

interface HomePageProps {
  onNavigate: (path: string) => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onNavigate }) => {
  return (
    <main
      style={{
        maxWidth: "1200px",
        margin: "0 auto",
        padding: "var(--space-8) var(--space-6)",
        width: "100%",
      }}
    >
      <section
        style={{
          textAlign: "center",
          marginBottom: "var(--space-12)",
        }}
      >
        <div
          style={{
            display: "inline-block",
            fontSize: "0.8125rem",
            fontWeight: 500,
            color: "var(--brand-primary)",
            backgroundColor: "var(--bg-tertiary)",
            border: "1px solid var(--border-muted)",
            padding: "4px 12px",
            borderRadius: "var(--radius-full)",
            marginBottom: "var(--space-4)",
          }}
        >
          Phase 1 Foundation Operational
        </div>
        <h1
          style={{
            fontSize: "2.5rem",
            fontWeight: 800,
            letterSpacing: "-0.025em",
            marginBottom: "var(--space-4)",
            lineHeight: 1.2,
          }}
        >
          DSAapp Engineering Architecture
        </h1>
        <p
          style={{
            fontSize: "1.125rem",
            color: "var(--text-secondary)",
            maxWidth: "720px",
            margin: "0 auto var(--space-6)",
            lineHeight: 1.6,
          }}
        >
          Production-grade, highly secure coding education ecosystem and online judge.
          Engineered under the strict 20% Theory / 80% Practice philosophy with zero fake metrics.
        </p>

        <div style={{ display: "flex", justifyContent: "center", gap: "var(--space-4)" }}>
          <button
            onClick={() => onNavigate("/status")}
            style={{
              backgroundColor: "var(--brand-primary)",
              color: "#ffffff",
              border: "none",
              borderRadius: "var(--radius-md)",
              padding: "var(--space-3) var(--space-6)",
              fontSize: "0.9375rem",
              fontWeight: 600,
              cursor: "pointer",
              boxShadow: "var(--shadow-glow)",
              transition: "background-color 0.15s ease",
            }}
          >
            Inspect Live Diagnostics
          </button>
        </div>
      </section>

      {/* Core Architectural Pillars */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "var(--space-6)",
          marginBottom: "var(--space-12)",
        }}
      >
        <div
          style={{
            backgroundColor: "var(--bg-card)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-3)",
              marginBottom: "var(--space-3)",
            }}
          >
            <span
              style={{
                backgroundColor: "var(--status-info-bg)",
                color: "var(--status-info)",
                padding: "6px 10px",
                borderRadius: "var(--radius-md)",
                fontSize: "0.875rem",
                fontWeight: 600,
              }}
            >
              01
            </span>
            <h2 style={{ fontSize: "1.125rem", fontWeight: 600 }}>Security-First Foundation</h2>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", lineHeight: 1.6 }}>
            Defensive headers (CSP, HSTS, X-Frame-Options), strict CORS allowlisting, client-payload size limits, and X-Request-ID correlation on every API request.
          </p>
        </div>

        <div
          style={{
            backgroundColor: "var(--bg-card)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-3)",
              marginBottom: "var(--space-3)",
            }}
          >
            <span
              style={{
                backgroundColor: "var(--status-success-bg)",
                color: "var(--status-success)",
                padding: "6px 10px",
                borderRadius: "var(--radius-md)",
                fontSize: "0.875rem",
                fontWeight: 600,
              }}
            >
              02
            </span>
            <h2 style={{ fontSize: "1.125rem", fontWeight: 600 }}>Dual Database Pipeline</h2>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", lineHeight: 1.6 }}>
            SQLAlchemy 2.0 asynchronous engine with zero-config async SQLite for dev/test and connection-pooled PostgreSQL with Alembic conventions for production.
          </p>
        </div>

        <div
          style={{
            backgroundColor: "var(--bg-card)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-3)",
              marginBottom: "var(--space-3)",
            }}
          >
            <span
              style={{
                backgroundColor: "var(--status-warning-bg)",
                color: "var(--status-warning)",
                padding: "6px 10px",
                borderRadius: "var(--radius-md)",
                fontSize: "0.875rem",
                fontWeight: 600,
              }}
            >
              03
            </span>
            <h2 style={{ fontSize: "1.125rem", fontWeight: 600 }}>Isolated Judge Boundary</h2>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", lineHeight: 1.6 }}>
            Strict architectural rule: Student code is never executed in-process. Future online judge execution routes to isolated sandboxes outside FastAPI.
          </p>
        </div>
      </section>
    </main>
  );
};
