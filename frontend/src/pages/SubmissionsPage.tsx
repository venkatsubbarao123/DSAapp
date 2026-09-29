import React, { useEffect, useState } from "react";
import { fetchApi } from "../services/apiClient.ts";
import { useAuth } from "../context/AuthContext.tsx";
import { SubmissionSummary } from "../types/progress.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";

interface SubmissionsPageProps {
  onNavigate: (path: string) => void;
}

export const SubmissionsPage: React.FC<SubmissionsPageProps> = ({ onNavigate }) => {
  const { isAuthenticated, openAuthModal } = useAuth();
  const [submissions, setSubmissions] = useState<SubmissionSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchApi<{ items: SubmissionSummary[]; total: number; skip: number; limit: number }>(
      "/api/v1/submissions?limit=50"
    )
      .then((res) => {
        if (!isMounted) return;
        setSubmissions(res.data.items || []);
        setTotal(res.data.total || 0);
      })
      .catch((err: unknown) => {
        if (!isMounted) return;
        const msg = err instanceof Error ? err.message : "Failed to load submissions.";
        setError(msg);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <main
        id="main-content"
        style={{
          flex: 1,
          maxWidth: "800px",
          margin: "var(--space-12) auto",
          padding: "0 var(--space-6)",
          textAlign: "center",
        }}
      >
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-xl)",
            padding: "var(--space-10) var(--space-8)",
          }}
        >
          <div style={{ fontSize: "3rem", marginBottom: "var(--space-4)" }}>📝</div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: "var(--space-3)" }}>
            Submission History
          </h1>
          <p
            style={{
              color: "var(--text-secondary)",
              fontSize: "1rem",
              lineHeight: 1.6,
              maxWidth: "520px",
              margin: "0 auto var(--space-6) auto",
            }}
          >
            Sign in to view your stored code submissions, submission timestamps, and language metadata.
          </p>
          <button
            onClick={() => openAuthModal("login")}
            style={{
              backgroundColor: "var(--brand-primary)",
              color: "#ffffff",
              border: "none",
              padding: "var(--space-3) var(--space-8)",
              borderRadius: "var(--radius-md)",
              fontWeight: 600,
              cursor: "pointer",
              fontSize: "1rem",
            }}
          >
            Sign In to View Submissions
          </button>
        </div>
      </main>
    );
  }

  if (loading) {
    return (
      <main id="main-content" style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center" }}>
        <LoadingSpinner size="lg" />
      </main>
    );
  }

  return (
    <main
      id="main-content"
      style={{
        flex: 1,
        maxWidth: "1140px",
        margin: "0 auto",
        padding: "var(--space-8) var(--space-6)",
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      {/* Page Title */}
      <div style={{ marginBottom: "var(--space-6)" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: "0 0 var(--space-2) 0", letterSpacing: "-0.025em" }}>
          Submission History
        </h1>
        <p style={{ color: "var(--text-secondary)", margin: 0, fontSize: "0.9375rem" }}>
          Immutable records of your submitted solutions, metadata, and status.
        </p>
      </div>

      {/* Prominent Educational Invariant Notice */}
      <div
        role="region"
        aria-label="Execution Policy Notice"
        style={{
          backgroundColor: "rgba(59, 130, 246, 0.08)",
          border: "1px solid rgba(59, 130, 246, 0.3)",
          borderRadius: "var(--radius-lg)",
          padding: "var(--space-4) var(--space-6)",
          marginBottom: "var(--space-6)",
          display: "flex",
          alignItems: "flex-start",
          gap: "var(--space-4)",
        }}
      >
        <span style={{ fontSize: "1.5rem", lineHeight: 1 }}>🛡️</span>
        <div>
          <h2 style={{ fontSize: "0.9375rem", fontWeight: 700, margin: "0 0 4px 0", color: "var(--brand-primary)" }}>
            Zero-Trust Architectural Invariant: Submissions are Queued
          </h2>
          <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
            In accordance with platform security invariants, arbitrary student code execution inside the API service is strictly disabled.
            Your code is safely stored, deduplicated via idempotency controls, and queued for future containerized judge execution (Phase 7).
            No unverified "Accepted" or "Wrong Answer" verdicts are fabricated.
          </p>
        </div>
      </div>

      {error && (
        <div
          role="alert"
          style={{
            backgroundColor: "var(--status-danger-bg)",
            border: "1px solid var(--status-danger)",
            color: "var(--status-danger)",
            padding: "var(--space-4)",
            borderRadius: "var(--radius-md)",
            marginBottom: "var(--space-6)",
          }}
        >
          {error}
        </div>
      )}

      {/* Submissions Table / Empty State */}
      {submissions.length === 0 ? (
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-xl)",
            padding: "var(--space-12) var(--space-6)",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "2.5rem", marginBottom: "var(--space-3)" }}>📁</div>
          <h3 style={{ fontSize: "1.125rem", fontWeight: 700, margin: "0 0 var(--space-2) 0" }}>
            No submissions recorded yet
          </h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginBottom: "var(--space-6)" }}>
            Select a problem from the curriculum and submit your solution code to start tracking your attempts.
          </p>
          <button
            onClick={() => onNavigate("/problems")}
            style={{
              backgroundColor: "var(--brand-primary)",
              color: "#ffffff",
              border: "none",
              padding: "var(--space-2) var(--space-6)",
              borderRadius: "var(--radius-md)",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Explore Problems →
          </button>
        </div>
      ) : (
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "var(--space-3) var(--space-6)",
              borderBottom: "1px solid var(--border-subtle)",
              fontSize: "0.8125rem",
              color: "var(--text-muted)",
              display: "flex",
              justifyContent: "space-between",
            }}
          >
            <span>Total Submissions: {total}</span>
            <span>Showing latest {submissions.length}</span>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-tertiary)" }}>
                  <th style={{ padding: "var(--space-3) var(--space-6)", fontWeight: 600, color: "var(--text-muted)" }}>
                    Problem
                  </th>
                  <th style={{ padding: "var(--space-3) var(--space-4)", fontWeight: 600, color: "var(--text-muted)" }}>
                    Language
                  </th>
                  <th style={{ padding: "var(--space-3) var(--space-4)", fontWeight: 600, color: "var(--text-muted)" }}>
                    Submitted At
                  </th>
                  <th style={{ padding: "var(--space-3) var(--space-4)", fontWeight: 600, color: "var(--text-muted)" }}>
                    Status
                  </th>
                  <th style={{ padding: "var(--space-3) var(--space-6)", textAlign: "right", fontWeight: 600, color: "var(--text-muted)" }}>
                    Action
                  </th>
                </tr>
              </thead>
              <tbody>
                {submissions.map((sub) => (
                  <tr
                    key={sub.id}
                    style={{
                      borderBottom: "1px solid var(--border-subtle)",
                      transition: "background-color 0.15s ease",
                    }}
                  >
                    <td style={{ padding: "var(--space-4) var(--space-6)", fontWeight: 600 }}>
                      <button
                        onClick={() => onNavigate(`/problems/${sub.problem_slug}`)}
                        style={{
                          background: "none",
                          border: "none",
                          padding: 0,
                          color: "var(--text-primary)",
                          fontWeight: 600,
                          fontSize: "0.875rem",
                          cursor: "pointer",
                          textAlign: "left",
                        }}
                      >
                        {sub.problem_title}
                      </button>
                    </td>
                    <td style={{ padding: "var(--space-4) var(--space-4)" }}>
                      <span
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.75rem",
                          padding: "2px 6px",
                          borderRadius: "var(--radius-sm)",
                          backgroundColor: "var(--bg-tertiary)",
                          color: "var(--text-secondary)",
                          border: "1px solid var(--border-subtle)",
                        }}
                      >
                        {sub.language}
                      </span>
                    </td>
                    <td style={{ padding: "var(--space-4) var(--space-4)", color: "var(--text-muted)", fontSize: "0.8125rem" }}>
                      {new Date(sub.created_at).toLocaleString()}
                    </td>
                    <td style={{ padding: "var(--space-4) var(--space-4)" }}>
                      <span
                        style={{
                          fontSize: "0.6875rem",
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: "var(--radius-full)",
                          backgroundColor:
                            sub.status === "QUEUED_FOR_FUTURE_JUDGE"
                              ? "rgba(59, 130, 246, 0.15)"
                              : "var(--bg-tertiary)",
                          color:
                            sub.status === "QUEUED_FOR_FUTURE_JUDGE"
                              ? "var(--brand-primary)"
                              : "var(--text-secondary)",
                          border: `1px solid ${
                            sub.status === "QUEUED_FOR_FUTURE_JUDGE"
                              ? "rgba(59, 130, 246, 0.3)"
                              : "var(--border-subtle)"
                          }`,
                        }}
                      >
                        {sub.status.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td style={{ padding: "var(--space-4) var(--space-6)", textAlign: "right" }}>
                      <button
                        onClick={() => onNavigate(`/submissions/${sub.public_id}`)}
                        style={{
                          backgroundColor: "var(--bg-tertiary)",
                          border: "1px solid var(--border-subtle)",
                          color: "var(--text-primary)",
                          padding: "4px 10px",
                          borderRadius: "var(--radius-md)",
                          fontSize: "0.75rem",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        View Code
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
  );
};
