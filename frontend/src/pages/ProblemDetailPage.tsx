import React, { useState, useEffect } from "react";
import { fetchApi, APIClientError } from "../services/apiClient.ts";
import { ProblemDetail, ProblemDifficulty } from "../types/curriculum.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";
import { PremiumGate } from "../components/common/PremiumGate.tsx";

interface ProblemDetailPageProps {
  problemId: string;
  onNavigate: (path: string) => void;
}

export const ProblemDetailPage: React.FC<ProblemDetailPageProps> = ({
  problemId,
  onNavigate,
}) => {
  const [problem, setProblem] = useState<ProblemDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isLocked, setIsLocked] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [revealedHints, setRevealedHints] = useState<Record<number, boolean>>({});

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setIsLocked(false);
    setError(null);

    fetchApi<ProblemDetail>(`/api/v1/problems/${problemId}`)
      .then((res) => {
        if (isMounted) setProblem(res.data);
      })
      .catch((err) => {
        if (!isMounted) return;
        if (err instanceof APIClientError && err.code === "HTTP_403") {
          setIsLocked(true);
        } else {
          setError(err.message || "Failed to load problem.");
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [problemId]);

  const toggleHint = (hintNum: number) => {
    setRevealedHints((prev) => ({ ...prev, [hintNum]: !prev[hintNum] }));
  };

  const difficultyColors = {
    EASY: "var(--status-success)",
    MEDIUM: "var(--status-warning)",
    HARD: "var(--status-danger)",
    EXPERT: "#a855f7",
  };

  if (loading) {
    return (
      <main id="main-content" style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center" }}>
        <LoadingSpinner size="lg" />
      </main>
    );
  }

  if (isLocked) {
    return (
      <main id="main-content" style={{ flex: 1, padding: "var(--space-8) var(--space-6)" }}>
        <PremiumGate contentType="problem" onUpgrade={() => onNavigate("/premium")} />
      </main>
    );
  }

  if (error || !problem) {
    return (
      <main id="main-content" style={{ flex: 1, padding: "var(--space-8) var(--space-6)", maxWidth: "800px", margin: "0 auto" }}>
        <div
          role="alert"
          style={{
            backgroundColor: "var(--status-danger-bg)",
            border: "1px solid var(--status-danger)",
            color: "var(--status-danger)",
            padding: "var(--space-4)",
            borderRadius: "var(--radius-md)",
            marginBottom: "var(--space-4)",
          }}
        >
          {error || "Problem not found."}
        </div>
        <button
          onClick={() => onNavigate("/problems")}
          style={{
            background: "none",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-primary)",
            padding: "var(--space-2) var(--space-4)",
            borderRadius: "var(--radius-md)",
            cursor: "pointer",
          }}
        >
          ← Return to Problems
        </button>
      </main>
    );
  }

  return (
    <main
      id="main-content"
      style={{
        flex: 1,
        maxWidth: "960px",
        margin: "0 auto",
        padding: "var(--space-8) var(--space-6)",
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      <button
        onClick={() => onNavigate("/problems")}
        style={{
          background: "none",
          border: "none",
          color: "var(--brand-primary)",
          fontWeight: 600,
          fontSize: "0.875rem",
          cursor: "pointer",
          marginBottom: "var(--space-6)",
          padding: 0,
        }}
      >
        ← Back to Problem Directory
      </button>

      {/* Problem Header */}
      <header style={{ marginBottom: "var(--space-8)", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "var(--space-6)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", flexWrap: "wrap", marginBottom: "var(--space-2)" }}>
          <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: 0, letterSpacing: "-0.025em" }}>
            {problem.title}
          </h1>
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: 700,
              padding: "2px 8px",
              borderRadius: "var(--radius-sm)",
              backgroundColor: "var(--bg-tertiary)",
              color: difficultyColors[problem.difficulty as ProblemDifficulty] || "var(--text-primary)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            {problem.difficulty}
          </span>
          {problem.access_level === "PREMIUM" && (
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 700,
                padding: "2px 8px",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "rgba(234, 179, 8, 0.15)",
                color: "var(--status-warning)",
                border: "1px solid var(--status-warning)",
              }}
            >
              PRO
            </span>
          )}
        </div>

        <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap", marginTop: "var(--space-3)" }}>
          {problem.patterns.map((pat) => (
            <span
              key={pat.id}
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                backgroundColor: "var(--bg-secondary)",
                color: "var(--brand-primary)",
                padding: "2px 8px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              Pattern: {pat.name}
            </span>
          ))}
          {problem.tags.map((t) => (
            <span
              key={t.id}
              style={{
                fontSize: "0.75rem",
                backgroundColor: "var(--bg-secondary)",
                color: "var(--text-muted)",
                padding: "2px 8px",
                borderRadius: "var(--radius-sm)",
              }}
            >
              #{t.name}
            </span>
          ))}
        </div>
      </header>

      {/* Problem Statement */}
      <section style={{ marginBottom: "var(--space-8)" }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "var(--space-3)" }}>
          Problem Description
        </h2>
        <div style={{ fontSize: "1rem", lineHeight: 1.7, color: "var(--text-primary)", whiteSpace: "pre-line" }}>
          {problem.statement}
        </div>
      </section>

      {/* Constraints Box */}
      {problem.constraints && (
        <section
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-4) var(--space-6)",
            marginBottom: "var(--space-8)",
          }}
        >
          <h3 style={{ fontSize: "0.875rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)", marginBottom: "var(--space-2)" }}>
            Constraints & Complexity
          </h3>
          <pre
            style={{
              margin: 0,
              fontFamily: "var(--font-mono)",
              fontSize: "0.875rem",
              lineHeight: 1.6,
              color: "var(--text-secondary)",
              whiteSpace: "pre-wrap",
            }}
          >
            {problem.constraints}
          </pre>
          {(problem.expected_time_complexity || problem.expected_space_complexity) && (
            <div style={{ marginTop: "var(--space-3)", fontSize: "0.8125rem", color: "var(--text-muted)", display: "flex", gap: "var(--space-4)" }}>
              {problem.expected_time_complexity && (
                <span>Expected Time: <strong style={{ color: "var(--text-primary)" }}>{problem.expected_time_complexity}</strong></span>
              )}
              {problem.expected_space_complexity && (
                <span>Expected Space: <strong style={{ color: "var(--text-primary)" }}>{problem.expected_space_complexity}</strong></span>
              )}
            </div>
          )}
        </section>
      )}

      {/* Examples */}
      {problem.examples.length > 0 && (
        <section style={{ marginBottom: "var(--space-8)" }}>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "var(--space-4)" }}>
            Examples
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
            {problem.examples.map((ex, idx) => (
              <div
                key={ex.id || idx}
                style={{
                  backgroundColor: "var(--bg-secondary)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-lg)",
                  padding: "var(--space-4) var(--space-6)",
                }}
              >
                <h4 style={{ margin: "0 0 var(--space-2) 0", fontSize: "0.875rem", color: "var(--brand-primary)" }}>
                  Example {ex.display_order || idx + 1}:
                </h4>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.875rem", display: "flex", flexDirection: "column", gap: "4px" }}>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Input: </span>
                    <span style={{ color: "var(--text-primary)" }}>{ex.input}</span>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Output: </span>
                    <span style={{ color: "var(--status-success)" }}>{ex.output}</span>
                  </div>
                </div>
                {ex.explanation && (
                  <p style={{ margin: "var(--space-2) 0 0 0", fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                    <strong>Explanation:</strong> {ex.explanation}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Sample Test Cases (Strictly Sample Only) */}
      {problem.sample_test_cases.length > 0 && (
        <section style={{ marginBottom: "var(--space-8)" }}>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "var(--space-3)" }}>
            Sample Verification Cases
          </h2>
          <div
            style={{
              backgroundColor: "var(--bg-tertiary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-4) var(--space-6)",
            }}
          >
            {problem.sample_test_cases.map((tc, idx) => (
              <div key={tc.id || idx} style={{ marginBottom: idx < problem.sample_test_cases.length - 1 ? "var(--space-4)" : 0 }}>
                <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  Case {tc.display_order}:
                </span>
                <pre style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize: "0.8125rem", color: "var(--text-primary)" }}>
                  Input: {tc.input} {"\n"}
                  Expected Output: {tc.expected_output}
                </pre>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Progressive Hints Accordion */}
      {problem.hints.length > 0 && (
        <section style={{ marginBottom: "var(--space-10)" }}>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "var(--space-4)" }}>
            Progressive Hints
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
            {problem.hints.map((hint) => (
              <div
                key={hint.id}
                style={{
                  backgroundColor: "var(--bg-secondary)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-md)",
                  overflow: "hidden",
                }}
              >
                <button
                  onClick={() => toggleHint(hint.hint_number)}
                  style={{
                    width: "100%",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "var(--space-3) var(--space-4)",
                    background: "none",
                    border: "none",
                    color: "var(--text-primary)",
                    fontSize: "0.875rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  <span style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                    <span>💡 Hint {hint.hint_number}: {hint.title}</span>
                    {hint.is_premium && (
                      <span style={{ fontSize: "0.6875rem", color: "var(--status-warning)", fontWeight: 700 }}>
                        PRO HINT
                      </span>
                    )}
                  </span>
                  <span>{revealedHints[hint.hint_number] ? "▲" : "▼"}</span>
                </button>
                {revealedHints[hint.hint_number] && (
                  <div
                    style={{
                      padding: "var(--space-3) var(--space-4)",
                      borderTop: "1px solid var(--border-subtle)",
                      fontSize: "0.875rem",
                      color: "var(--text-secondary)",
                      lineHeight: 1.6,
                      backgroundColor: "var(--bg-tertiary)",
                    }}
                  >
                    {hint.content}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Educational Notice on Online Judge Boundary */}
      <div
        style={{
          border: "1px dashed var(--border-muted)",
          borderRadius: "var(--radius-lg)",
          padding: "var(--space-4) var(--space-6)",
          fontSize: "0.8125rem",
          color: "var(--text-muted)",
          lineHeight: 1.5,
        }}
      >
        <strong>Architectural Notice:</strong> This problem view displays the educational specification, constraints, and sample test cases.
        As specified in the system invariants, in-process code execution is strictly prohibited. The containerized execution sandbox will be introduced in Phase 7.
      </div>
    </main>
  );
};
