import React, { useEffect, useState } from "react";
import { fetchApi, APIClientError } from "../services/apiClient.ts";
import { HealthData } from "../types/api.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";

export const SystemStatusPage: React.FC = () => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    const start = performance.now();
    try {
      const response = await fetchApi<HealthData>("/api/v1/health");
      const elapsed = Math.round(performance.now() - start);
      setHealth(response.data);
      setRequestId(response.request_id || null);
      setLatencyMs(elapsed);
    } catch (err) {
      if (err instanceof APIClientError) {
        setError(err.message);
        setRequestId(err.requestId || null);
      } else {
        setError("Failed to query API health endpoint.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void checkHealth();
  }, []);

  return (
    <main
      style={{
        maxWidth: "960px",
        margin: "0 auto",
        padding: "var(--space-8) var(--space-6)",
        width: "100%",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "var(--space-6)",
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, marginBottom: "var(--space-1)" }}>
            System Vitality & Diagnostics
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
            Real-time health telemetry queried directly from backend <code style={{ fontFamily: "var(--font-mono)" }}>/api/v1/health</code>.
          </p>
        </div>
        <button
          onClick={checkHealth}
          disabled={loading}
          style={{
            backgroundColor: "var(--bg-tertiary)",
            color: "var(--text-primary)",
            border: "1px solid var(--border-muted)",
            borderRadius: "var(--radius-md)",
            padding: "var(--space-2) var(--space-4)",
            fontSize: "0.875rem",
            fontWeight: 500,
            cursor: loading ? "not-allowed" : "pointer",
            transition: "all 0.15s ease",
          }}
        >
          {loading ? "Checking..." : "Refresh Status"}
        </button>
      </div>

      {loading && !health && (
        <div style={{ textAlign: "center", padding: "var(--space-12)" }}>
          <LoadingSpinner label="Querying backend health..." size="lg" />
        </div>
      )}

      {error && (
        <div
          role="alert"
          style={{
            backgroundColor: "var(--status-danger-bg)",
            border: "1px solid var(--status-danger)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
            marginBottom: "var(--space-6)",
          }}
        >
          <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--status-danger)", marginBottom: "var(--space-2)" }}>
            Service Connectivity Alert
          </h2>
          <p style={{ color: "var(--text-primary)", fontSize: "0.875rem", marginBottom: "var(--space-4)" }}>
            {error}
          </p>
          {requestId && (
            <p style={{ color: "var(--text-muted)", fontSize: "0.75rem", fontFamily: "var(--font-mono)" }}>
              Correlation Request ID: {requestId}
            </p>
          )}
        </div>
      )}

      {health && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
          {/* Status summary banner */}
          <div
            style={{
              backgroundColor: health.status === "healthy" ? "var(--status-success-bg)" : "var(--status-warning-bg)",
              border: `1px solid ${health.status === "healthy" ? "var(--status-success)" : "var(--status-warning)"}`,
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-6)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)" }}>
                Overall Operational State
              </div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, textTransform: "capitalize", color: health.status === "healthy" ? "var(--status-success)" : "var(--status-warning)" }}>
                {health.status}
              </div>
            </div>
            {latencyMs !== null && (
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "var(--text-muted)" }}>
                  Probe Roundtrip
                </div>
                <div style={{ fontSize: "1.25rem", fontWeight: 600, fontFamily: "var(--font-mono)" }}>
                  {latencyMs} ms
                </div>
              </div>
            )}
          </div>

          {/* Subsystem Grid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
              gap: "var(--space-4)",
            }}
          >
            <div
              style={{
                backgroundColor: "var(--bg-card)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                padding: "var(--space-5)",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "var(--space-1)" }}>
                API Service
              </div>
              <div style={{ fontSize: "1.125rem", fontWeight: 600 }}>{health.service}</div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "var(--space-2)" }}>
                Environment: <code style={{ fontFamily: "var(--font-mono)" }}>{health.environment}</code>
              </div>
            </div>

            <div
              style={{
                backgroundColor: "var(--bg-card)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                padding: "var(--space-5)",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "var(--space-1)" }}>
                Relational Database
              </div>
              <div
                style={{
                  fontSize: "1.125rem",
                  fontWeight: 600,
                  color: health.database === "connected" ? "var(--status-success)" : "var(--status-danger)",
                }}
              >
                {health.database}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "var(--space-2)" }}>
                Dialect: SQLite / PostgreSQL Async
              </div>
            </div>

            <div
              style={{
                backgroundColor: "var(--bg-card)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                padding: "var(--space-5)",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "var(--space-1)" }}>
                Cache / Broker
              </div>
              <div style={{ fontSize: "1.125rem", fontWeight: 600 }}>{health.redis}</div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "var(--space-2)" }}>
                Status: Optional for Phase 1
              </div>
            </div>
          </div>

          {/* Trace correlation panel */}
          {requestId && (
            <div
              style={{
                backgroundColor: "var(--bg-card)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                padding: "var(--space-4) var(--space-5)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                fontSize: "0.8125rem",
              }}
            >
              <span style={{ color: "var(--text-muted)" }}>Trace Correlation ID:</span>
              <code style={{ fontFamily: "var(--font-mono)", color: "var(--brand-primary)" }}>{requestId}</code>
            </div>
          )}
        </div>
      )}
    </main>
  );
};
