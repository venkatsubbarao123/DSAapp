import React, { useEffect, useState } from "react";
import { fetchApi } from "../services/apiClient.ts";
import { HealthData } from "../types/api.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";

interface ServiceStatus {
  label: string;
  status: "operational" | "degraded" | "down" | "loading";
  description: string;
}

export const SystemStatusPage: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [overallOk, setOverallOk] = useState<boolean | null>(null);
  const [services, setServices] = useState<ServiceStatus[]>([
    { label: "API", status: "loading", description: "Backend API server" },
    { label: "Database", status: "loading", description: "Data persistence layer" },
    { label: "Judge", status: "loading", description: "Secure code execution sandbox" },
    { label: "AI Tutor", status: "loading", description: "AI learning assistance" },
  ]);

  const checkHealth = async () => {
    setLoading(true);
    try {
      const response = await fetchApi<HealthData>("/api/v1/health", {}, 5000);
      const h = response.data;
      const ok = h?.status === "healthy";
      setOverallOk(ok);

      setServices([
        {
          label: "API",
          status: ok ? "operational" : "degraded",
          description: "Backend API server",
        },
        {
          label: "Database",
          status: h?.database === "connected" ? "operational" : "degraded",
          description: "Data persistence layer",
        },
        {
          label: "Judge",
          status: "operational",
          description: "Secure code execution sandbox",
        },
        {
          label: "AI Tutor",
          status: "operational",
          description: "AI learning assistance",
        },
      ]);
    } catch {
      setOverallOk(false);
      setServices([
        { label: "API", status: "down", description: "Backend API server" },
        { label: "Database", status: "loading", description: "Data persistence layer" },
        { label: "Judge", status: "loading", description: "Secure code execution sandbox" },
        { label: "AI Tutor", status: "loading", description: "AI learning assistance" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void checkHealth();
  }, []);

  const statusColor = (s: ServiceStatus["status"]) => {
    if (s === "operational") return "var(--status-success)";
    if (s === "degraded") return "var(--status-warning)";
    if (s === "down") return "var(--status-danger)";
    return "var(--text-muted)";
  };

  const statusLabel = (s: ServiceStatus["status"]) => {
    if (s === "operational") return "Operational";
    if (s === "degraded") return "Degraded";
    if (s === "down") return "Down";
    return "Checking…";
  };

  return (
    <main
      style={{
        maxWidth: "720px",
        margin: "0 auto",
        padding: "var(--space-8) var(--space-6)",
        width: "100%",
      }}
    >
      <div style={{ marginBottom: "var(--space-8)", textAlign: "center" }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, marginBottom: "var(--space-2)" }}>
          System Vitality & Diagnostics
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.9375rem" }}>
          Current operational status of DSAapp services.
        </p>
      </div>

      {/* Overall banner */}
      {overallOk !== null && (
        <div
          style={{
            backgroundColor: overallOk ? "var(--status-success-bg)" : "var(--status-danger-bg)",
            border: `1px solid ${overallOk ? "var(--status-success)" : "var(--status-danger)"}`,
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-5) var(--space-6)",
            display: "flex",
            alignItems: "center",
            gap: "var(--space-3)",
            marginBottom: "var(--space-6)",
          }}
        >
          <span style={{ fontSize: "1.5rem" }}>{overallOk ? "✅" : "⚠️"}</span>
          <div>
            <div
              style={{
                fontWeight: 700,
                fontSize: "1.0625rem",
                color: overallOk ? "var(--status-success)" : "var(--status-danger)",
              }}
            >
              {overallOk ? "All Systems Operational" : "Service Disruption Detected"}
            </div>
            <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginTop: "2px" }}>
              Last checked just now
            </div>
          </div>
        </div>
      )}

      {loading && overallOk === null && (
        <div style={{ display: "flex", justifyContent: "center", padding: "var(--space-8)" }}>
          <LoadingSpinner size="lg" label="Checking service status…" />
        </div>
      )}

      {/* Service grid */}
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
        {services.map((svc) => (
          <div
            key={svc.label}
            style={{
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              padding: "var(--space-4) var(--space-6)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: "0.9375rem" }}>{svc.label}</div>
              <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginTop: "2px" }}>
                {svc.description}
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              {svc.status !== "loading" && (
                <span
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "var(--radius-full)",
                    backgroundColor: statusColor(svc.status),
                    display: "inline-block",
                  }}
                />
              )}
              <span
                style={{
                  fontSize: "0.8125rem",
                  fontWeight: 600,
                  color: svc.status === "loading" ? "var(--text-muted)" : statusColor(svc.status),
                }}
              >
                {statusLabel(svc.status)}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: "var(--space-6)", textAlign: "center" }}>
        <button
          onClick={checkHealth}
          disabled={loading}
          style={{
            backgroundColor: "var(--bg-tertiary)",
            color: "var(--text-primary)",
            border: "1px solid var(--border-muted)",
            borderRadius: "var(--radius-md)",
            padding: "var(--space-2) var(--space-6)",
            fontSize: "0.875rem",
            fontWeight: 500,
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? "Checking…" : "Refresh Status"}
        </button>
      </div>
    </main>
  );
};
