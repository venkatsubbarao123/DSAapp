import React, { useState, useEffect } from "react";
import { fetchApi } from "../services/apiClient.ts";
import { CurriculumSummary } from "../types/curriculum.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";

interface CurriculumPageProps {
  onNavigate: (path: string) => void;
}

export const CurriculumPage: React.FC<CurriculumPageProps> = ({ onNavigate }) => {
  const [curricula, setCurricula] = useState<CurriculumSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    fetchApi<CurriculumSummary[]>("/api/v1/curricula")
      .then((res) => {
        if (isMounted) setCurricula(res.data || []);
      })
      .catch((err) => {
        if (isMounted) setError(err.message || "Failed to load curricula.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <main
      id="main-content"
      style={{
        flex: 1,
        maxWidth: "1100px",
        margin: "0 auto",
        padding: "var(--space-8) var(--space-6)",
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      <section style={{ marginBottom: "var(--space-10)" }}>
        <div
          style={{
            display: "inline-block",
            fontSize: "0.8125rem",
            fontWeight: 600,
            color: "var(--brand-primary)",
            backgroundColor: "var(--bg-tertiary)",
            border: "1px solid var(--border-muted)",
            padding: "4px 12px",
            borderRadius: "var(--radius-full)",
            marginBottom: "var(--space-4)",
          }}
        >
          Learning Paths
        </div>
        <h1
          style={{
            fontSize: "2.25rem",
            fontWeight: 800,
            letterSpacing: "-0.025em",
            marginBottom: "var(--space-3)",
          }}
        >
          Structured Learning Pathways
        </h1>
        <p
          style={{
            fontSize: "1.0625rem",
            color: "var(--text-secondary)",
            maxWidth: "700px",
            lineHeight: 1.6,
          }}
        >
          Choose a structured path and go step-by-step from beginner to interview-ready.
          Each curriculum includes lessons, examples, exercises, and real coding problems.
        </p>
      </section>

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

      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "var(--space-12)" }}>
          <LoadingSpinner size="lg" />
        </div>
      ) : curricula.length === 0 ? (
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-10)",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "3rem", marginBottom: "var(--space-4)" }}>📚</div>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 600, marginBottom: "var(--space-2)" }}>
            Curriculum coming soon
          </h2>
          <p style={{ color: "var(--text-muted)", marginBottom: "var(--space-6)" }}>
            We're preparing structured learning paths. Start exploring topics in the meantime.
          </p>
          <button
            onClick={() => onNavigate("/topics")}
            style={{
              backgroundColor: "var(--brand-primary)",
              color: "#ffffff",
              border: "none",
              borderRadius: "var(--radius-md)",
              padding: "var(--space-2) var(--space-6)",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Explore Topics
          </button>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
          {curricula.map((curr) => (
            <div
              key={curr.id}
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-xl)",
                padding: "var(--space-8)",
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-4)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "var(--space-2)" }}>
                <h2 style={{ fontSize: "1.375rem", fontWeight: 700, margin: 0 }}>
                  {curr.title}
                </h2>
                <div style={{ display: "flex", gap: "var(--space-2)" }}>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      padding: "2px 8px",
                      borderRadius: "var(--radius-sm)",
                      backgroundColor: "var(--bg-tertiary)",
                      color: "var(--brand-primary)",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    {curr.level}
                  </span>
                  {curr.is_free && (
                    <span
                      style={{
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        padding: "2px 8px",
                        borderRadius: "var(--radius-sm)",
                        backgroundColor: "var(--status-success-bg)",
                        color: "var(--status-success)",
                        border: "1px solid var(--status-success)",
                      }}
                    >
                      FREE ACCESS
                    </span>
                  )}
                </div>
              </div>

              <p style={{ color: "var(--text-secondary)", fontSize: "0.9375rem", margin: 0, lineHeight: 1.6 }}>
                {curr.short_description || "Comprehensive algorithmic track."}
              </p>

              <div style={{ display: "flex", gap: "var(--space-4)", marginTop: "var(--space-2)" }}>
                <button
                  onClick={() => onNavigate(`/topics`)}
                  style={{
                    backgroundColor: "var(--brand-primary)",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "var(--radius-md)",
                    padding: "var(--space-2) var(--space-5)",
                    fontWeight: 600,
                    fontSize: "0.875rem",
                    cursor: "pointer",
                  }}
                >
                  Explore Topics
                </button>
                <button
                  onClick={() => onNavigate(`/problems`)}
                  style={{
                    background: "none",
                    color: "var(--text-primary)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    padding: "var(--space-2) var(--space-5)",
                    fontWeight: 500,
                    fontSize: "0.875rem",
                    cursor: "pointer",
                  }}
                >
                  View Problems
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
};
