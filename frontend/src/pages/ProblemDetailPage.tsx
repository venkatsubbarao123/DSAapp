import React, { useState, useEffect } from "react";
import { fetchApi, APIClientError } from "../services/apiClient.ts";
import { useAuth } from "../context/AuthContext.tsx";
import { ProblemDetail, ProblemDifficulty } from "../types/curriculum.ts";
import { ProblemProgress, SubmissionDetail, SubmissionResult, SubmissionStatus, MistakeType } from "../types/progress.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";
import { PremiumGate } from "../components/common/PremiumGate.tsx";

interface ProblemDetailPageProps {
  problemId: string;
  onNavigate: (path: string) => void;
}

const DEFAULT_STARTER_CODE: Record<string, string> = {
  python: `# Solution for problem in Python 3\nclass Solution:\n    def solve(self, *args):\n        # Your solution here\n        pass\n`,
  javascript: `// Solution in JavaScript (Node.js)\nfunction solve(...args) {\n  // Your solution here\n}\n`,
  typescript: `// Solution in TypeScript\nfunction solve(...args: any[]): any {\n  // Your solution here\n}\n`,
  java: `// Solution in Java\nclass Solution {\n    public void solve() {\n        // Your solution here\n    }\n}\n`,
  cpp: `// Solution in C++\n#include <iostream>\nusing namespace std;\n\nclass Solution {\npublic:\n    void solve() {\n        // Your solution here\n    }\n};\n`,
};

export const ProblemDetailPage: React.FC<ProblemDetailPageProps> = ({
  problemId,
  onNavigate,
}) => {
  const { isAuthenticated, openAuthModal } = useAuth();
  const [problem, setProblem] = useState<ProblemDetail | null>(null);
  const [progress, setProgress] = useState<ProblemProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [isLocked, setIsLocked] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [revealedHints, setRevealedHints] = useState<Record<number, boolean>>({});

  // Submission State
  const [language, setLanguage] = useState<string>("python");
  const [sourceCode, setSourceCode] = useState<string>(DEFAULT_STARTER_CODE.python);
  const [submitting, setSubmitting] = useState(false);
  const [submissionFeedback, setSubmissionFeedback] = useState<SubmissionDetail | null>(null);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [judgingStatus, setJudgingStatus] = useState<SubmissionStatus | null>(null);
  const [submissionResult, setSubmissionResult] = useState<SubmissionResult | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  // Mistake modal
  const [showMistakeModal, setShowMistakeModal] = useState(false);
  const [mistakeTitle, setMistakeTitle] = useState("");
  const [mistakeType, setMistakeType] = useState<MistakeType>("LOGIC_ERROR");
  const [mistakeDesc, setMistakeDesc] = useState("");
  const [mistakeCorrection, setMistakeCorrection] = useState("");
  const [mistakeSubmitting, setMistakeSubmitting] = useState(false);
  const [mistakeSuccess, setMistakeSuccess] = useState(false);

  // Revision Quick Add State
  const [revisionAdded, setRevisionAdded] = useState(false);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setIsLocked(false);
    setError(null);

    fetchApi<ProblemDetail>(`/api/v1/problems/${problemId}`)
      .then((res) => {
        if (!isMounted) return;
        setProblem(res.data);

        // If user is authenticated, fetch progress for this problem
        if (isAuthenticated) {
          fetchApi<ProblemProgress>(`/api/v1/progress/problems/${res.data.id}`)
            .then((progRes) => {
              if (isMounted) setProgress(progRes.data);
            })
            .catch(() => {
              // Ignore failure to fetch optional progress
            });
        }
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
  }, [problemId, isAuthenticated]);

  const toggleHint = (hintNum: number) => {
    setRevealedHints((prev) => ({ ...prev, [hintNum]: !prev[hintNum] }));
  };

  const handleLanguageChange = (newLang: string) => {
    setLanguage(newLang);
    setSourceCode(DEFAULT_STARTER_CODE[newLang] || "");
  };

  const handleSubmitCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAuthenticated) {
      openAuthModal("login");
      return;
    }
    if (!problem) return;

    // Client-side 64KB UTF-8 check
    const utf8Bytes = new TextEncoder().encode(sourceCode);
    if (utf8Bytes.length > 65536) {
      setSubmissionError("Source code exceeds maximum allowed size of 64KB.");
      return;
    }

    setSubmitting(true);
    setSubmissionError(null);
    setSubmissionFeedback(null);
    setJudgingStatus(null);
    setSubmissionResult(null);

    const idempotencyKey = `sub_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

    try {
      const res = await fetchApi<SubmissionDetail>("/api/v1/submissions", {
        method: "POST",
        headers: {
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify({
          problem_id: problem.id,
          language,
          source_code: sourceCode,
        }),
      });

      setSubmissionFeedback(res.data);
      setJudgingStatus(res.data.status);
      setSubmissionResult(res.data.result || null);

      // Advance progress to ATTEMPTED
      setProgress((prev) =>
        prev
          ? {
              ...prev,
              status: prev.status === "SOLVED" ? "SOLVED" : "ATTEMPTED",
              attempts_count: prev.attempts_count + 1,
              last_attempted_at: new Date().toISOString(),
            }
          : null
      );

      // Start polling for judge verdict if still queued or judging
      const terminalStatuses = [
        "ACCEPTED",
        "WRONG_ANSWER",
        "TIME_LIMIT_EXCEEDED",
        "MEMORY_LIMIT_EXCEEDED",
        "RUNTIME_ERROR",
        "COMPILATION_ERROR",
        "OUTPUT_LIMIT_EXCEEDED",
        "SYSTEM_ERROR",
        "CANCELLED",
      ];

      if (!terminalStatuses.includes(res.data.status)) {
        setIsPolling(true);
        let attempts = 0;
        const maxAttempts = 15;
        const pollInterval = setInterval(async () => {
          attempts += 1;
          try {
            const detailRes = await fetchApi<SubmissionDetail>(`/api/v1/submissions/${res.data.id}`);
            if (detailRes.data) {
              setJudgingStatus(detailRes.data.status);
              if (detailRes.data.result) {
                setSubmissionResult(detailRes.data.result);
              }
              if (terminalStatuses.includes(detailRes.data.status) || attempts >= maxAttempts) {
                clearInterval(pollInterval);
                setIsPolling(false);
                if (detailRes.data.status === "ACCEPTED" || detailRes.data.result?.verdict === "ACCEPTED") {
                  setProgress((prev) =>
                    prev
                      ? {
                          ...prev,
                          status: "SOLVED",
                          successful_attempts: prev.successful_attempts + 1,
                          solved_at: new Date().toISOString(),
                        }
                      : null
                  );
                }
              }
            }
          } catch {
            if (attempts >= maxAttempts) {
              clearInterval(pollInterval);
              setIsPolling(false);
            }
          }
        }, 1200);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to record submission.";
      setSubmissionError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddToRevision = async () => {
    if (!problem || !isAuthenticated) {
      openAuthModal("login");
      return;
    }

    try {
      await fetchApi("/api/v1/revision/items", {
        method: "POST",
        body: JSON.stringify({
          source_type: "PROBLEM",
          source_id: problem.id,
          title: problem.title,
        }),
      });
      setRevisionAdded(true);
      setTimeout(() => setRevisionAdded(false), 3000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to schedule for revision.");
    }
  };

  const handleSaveMistake = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!problem) return;
    setMistakeSubmitting(true);

    try {
      await fetchApi("/api/v1/mistakes", {
        method: "POST",
        body: JSON.stringify({
          problem_id: problem.id,
          mistake_type: mistakeType,
          title: mistakeTitle.trim(),
          description: mistakeDesc.trim(),
          correction: mistakeCorrection.trim() || undefined,
        }),
      });

      setMistakeSuccess(true);
      setTimeout(() => {
        setShowMistakeModal(false);
        setMistakeSuccess(false);
        setMistakeTitle("");
        setMistakeDesc("");
        setMistakeCorrection("");
      }, 1500);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to save mistake.");
    } finally {
      setMistakeSubmitting(false);
    }
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
        maxWidth: "1000px",
        margin: "0 auto",
        padding: "var(--space-8) var(--space-6)",
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-6)" }}>
        <button
          onClick={() => onNavigate("/problems")}
          style={{
            background: "none",
            border: "none",
            color: "var(--brand-primary)",
            fontWeight: 600,
            fontSize: "0.875rem",
            cursor: "pointer",
            padding: 0,
          }}
        >
          ← Back to Problem Directory
        </button>

        {/* Action buttons */}
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <button
            onClick={handleAddToRevision}
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              color: "var(--text-secondary)",
              padding: "4px 10px",
              borderRadius: "var(--radius-md)",
              fontSize: "0.75rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            {revisionAdded ? "✓ Added to Revision" : "+ Spaced Review"}
          </button>
          <button
            onClick={() => {
              if (!isAuthenticated) {
                openAuthModal("login");
                return;
              }
              setMistakeTitle(`Issue with ${problem.title}`);
              setShowMistakeModal(true);
            }}
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              color: "var(--text-secondary)",
              padding: "4px 10px",
              borderRadius: "var(--radius-md)",
              fontSize: "0.75rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            + Log Mistake
          </button>
        </div>
      </div>

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

          {/* User Progress Status Pill */}
          {isAuthenticated && progress && (
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 700,
                padding: "2px 8px",
                borderRadius: "var(--radius-full)",
                backgroundColor:
                  progress.status === "SOLVED"
                    ? "var(--status-success-bg)"
                    : progress.status === "ATTEMPTED"
                    ? "rgba(59, 130, 246, 0.15)"
                    : "var(--bg-tertiary)",
                color:
                  progress.status === "SOLVED"
                    ? "var(--status-success)"
                    : progress.status === "ATTEMPTED"
                    ? "var(--brand-primary)"
                    : "var(--text-muted)",
                border: "1px solid currentColor",
              }}
            >
              Status: {progress.status} (Attempts: {progress.attempts_count})
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
      {problem.sample_test_cases && problem.sample_test_cases.length > 0 && (
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
        <section style={{ marginBottom: "var(--space-8)" }}>
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

      {/* Phase 4 Solution Submission Box */}
      <section style={{ marginBottom: "var(--space-8)" }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "var(--space-3)" }}>
          Submit Solution Code
        </h2>

        {/* Security invariant explanation */}
        <div
          style={{
            backgroundColor: "rgba(59, 130, 246, 0.08)",
            border: "1px solid rgba(59, 130, 246, 0.3)",
            borderRadius: "var(--radius-md)",
            padding: "var(--space-3) var(--space-4)",
            marginBottom: "var(--space-4)",
            fontSize: "0.8125rem",
            color: "var(--text-secondary)",
          }}
        >
          <strong>Notice:</strong> Submissions in Phase 4 are securely stored and queued for future judge execution.
          In-process code execution is disabled. Attempting a problem automatically updates your progress status.
        </div>

        {submissionFeedback && (
          <div
            role="region"
            aria-label="Submission Result"
            style={{
              backgroundColor:
                submissionResult?.verdict === "ACCEPTED"
                  ? "rgba(35, 134, 54, 0.15)"
                  : submissionResult?.verdict
                  ? "rgba(218, 54, 51, 0.15)"
                  : "var(--status-success-bg)",
              border: `1px solid ${
                submissionResult?.verdict === "ACCEPTED"
                  ? "#238636"
                  : submissionResult?.verdict
                  ? "#da3633"
                  : "var(--status-success)"
              }`,
              color:
                submissionResult?.verdict === "ACCEPTED"
                  ? "#3fb950"
                  : submissionResult?.verdict
                  ? "#f85149"
                  : "var(--status-success)",
              padding: "var(--space-4)",
              borderRadius: "var(--radius-md)",
              marginBottom: "var(--space-4)",
              fontSize: "0.875rem",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "var(--space-2)" }}>
              <div>
                <div style={{ fontWeight: 700, marginBottom: "4px" }}>
                  ✓ Submission Received & Queued!
                </div>
                {submissionResult ? (
                  <div
                    style={{
                      fontWeight: 700,
                      fontSize: "1rem",
                      color: submissionResult.verdict === "ACCEPTED" ? "#3fb950" : "#f85149",
                    }}
                  >
                    {submissionResult.verdict === "ACCEPTED" ? "✓ Accepted" : `✗ ${submissionResult.verdict.replace(/_/g, " ")}`}
                  </div>
                ) : isPolling ? (
                  <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                    ⏳ Judging in Progress ({judgingStatus || "QUEUED"})...
                  </div>
                ) : null}
              </div>
              <span
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  padding: "2px 8px",
                  borderRadius: "var(--radius-full)",
                  backgroundColor:
                    submissionResult?.verdict === "ACCEPTED"
                      ? "rgba(35, 134, 54, 0.3)"
                      : "rgba(255, 255, 255, 0.1)",
                  color: "#ffffff",
                }}
              >
                {judgingStatus || submissionFeedback.status}
              </span>
            </div>

            <div style={{ fontSize: "0.8125rem", color: "var(--text-primary)", marginBottom: "var(--space-2)" }}>
              ID: <span style={{ fontFamily: "var(--font-mono)" }}>{submissionFeedback.public_id}</span> • Status:{" "}
              <strong>{judgingStatus || submissionFeedback.status}</strong>
            </div>

            {/* Execution Metrics Grid */}
            {submissionResult && (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                  gap: "var(--space-3)",
                  margin: "var(--space-3) 0",
                  padding: "var(--space-3)",
                  backgroundColor: "rgba(0, 0, 0, 0.2)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "0.8125rem",
                }}
              >
                <div>
                  <span style={{ color: "var(--text-secondary)", display: "block" }}>Test Cases</span>
                  <strong style={{ fontSize: "1rem" }}>
                    {submissionResult.tests_passed} / {submissionResult.tests_total}
                  </strong>
                </div>
                <div>
                  <span style={{ color: "var(--text-secondary)", display: "block" }}>Runtime</span>
                  <strong style={{ fontSize: "1rem" }}>{submissionResult.execution_time_ms ?? 0} ms</strong>
                </div>
                <div>
                  <span style={{ color: "var(--text-secondary)", display: "block" }}>Memory</span>
                  <strong style={{ fontSize: "1rem" }}>
                    {Math.round((submissionResult.memory_used_bytes ?? 0) / (1024 * 1024))} MB
                  </strong>
                </div>
              </div>
            )}

            {/* Error logs */}
            {(submissionResult?.compiler_output_safe || submissionResult?.runtime_output_safe) && (
              <div style={{ marginTop: "var(--space-3)" }}>
                <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                  Execution Details / Logs:
                </span>
                <pre
                  style={{
                    backgroundColor: "#0d1117",
                    border: "1px solid #30363d",
                    borderRadius: "var(--radius-sm)",
                    padding: "var(--space-3)",
                    fontSize: "0.75rem",
                    color: "#f85149",
                    maxHeight: "150px",
                    overflowY: "auto",
                    whiteSpace: "pre-wrap",
                    marginTop: "4px",
                  }}
                >
                  {submissionResult.compiler_output_safe || submissionResult.runtime_output_safe}
                </pre>
              </div>
            )}

            <div style={{ fontSize: "0.75rem", marginTop: "var(--space-2)", color: "var(--text-secondary)" }}>
              {submissionFeedback.execution_notice}
            </div>

            <button
              onClick={() => onNavigate(`/submissions/${submissionFeedback.public_id}`)}
              style={{
                marginTop: "var(--space-2)",
                background: "none",
                border: "none",
                padding: 0,
                color: "var(--brand-primary)",
                fontWeight: 600,
                cursor: "pointer",
                fontSize: "0.8125rem",
              }}
            >
              View in Submission History →
            </button>
          </div>
        )}

        {submissionError && (
          <div
            role="alert"
            style={{
              backgroundColor: "var(--status-danger-bg)",
              border: "1px solid var(--status-danger)",
              color: "var(--status-danger)",
              padding: "var(--space-3) var(--space-4)",
              borderRadius: "var(--radius-md)",
              marginBottom: "var(--space-4)",
              fontSize: "0.8125rem",
            }}
          >
            {submissionError}
          </div>
        )}

        <form onSubmit={handleSubmitCode}>
          <div
            style={{
              backgroundColor: "#161b22",
              border: "1px solid #30363d",
              borderRadius: "var(--radius-lg)",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "var(--space-2) var(--space-4)",
                backgroundColor: "#0d1117",
                borderBottom: "1px solid #30363d",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                <label style={{ fontSize: "0.75rem", color: "#8b949e", fontWeight: 600 }}>Language:</label>
                <select
                  value={language}
                  onChange={(e) => handleLanguageChange(e.target.value)}
                  style={{
                    backgroundColor: "#21262d",
                    color: "#c9d1d9",
                    border: "1px solid #30363d",
                    borderRadius: "var(--radius-sm)",
                    padding: "2px 8px",
                    fontSize: "0.8125rem",
                  }}
                  aria-label="Select programming language"
                >
                  <option value="python">Python 3</option>
                  <option value="javascript">JavaScript (Node.js)</option>
                  <option value="typescript">TypeScript</option>
                  <option value="java">Java 17</option>
                  <option value="cpp">C++20</option>
                </select>
              </div>

              <span style={{ fontSize: "0.75rem", color: "#8b949e", fontFamily: "var(--font-mono)" }}>
                {new TextEncoder().encode(sourceCode).length} / 65536 bytes
              </span>
            </div>

            <textarea
              value={sourceCode}
              onChange={(e) => setSourceCode(e.target.value)}
              rows={12}
              spellCheck={false}
              style={{
                width: "100%",
                padding: "var(--space-4)",
                backgroundColor: "#0d1117",
                color: "#c9d1d9",
                fontFamily: "var(--font-mono)",
                fontSize: "0.875rem",
                lineHeight: 1.6,
                border: "none",
                outline: "none",
                resize: "vertical",
                boxSizing: "border-box",
              }}
              placeholder="Write your code here..."
              aria-label="Code editor"
            />
          </div>

          <div style={{ marginTop: "var(--space-4)", display: "flex", justifyContent: "flex-end" }}>
            <button
              type="submit"
              disabled={submitting}
              style={{
                backgroundColor: "var(--brand-primary)",
                color: "#ffffff",
                border: "none",
                padding: "var(--space-3) var(--space-6)",
                borderRadius: "var(--radius-md)",
                fontWeight: 600,
                cursor: "pointer",
                fontSize: "0.875rem",
              }}
            >
              {submitting ? "Queuing Submission..." : "Submit Code (Queue for Judge)"}
            </button>
          </div>
        </form>
      </section>

      {/* Mistake Modal */}
      {showMistakeModal && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="problem-mistake-title"
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 100,
            padding: "var(--space-4)",
          }}
        >
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-xl)",
              maxWidth: "540px",
              width: "100%",
              padding: "var(--space-6)",
              boxSizing: "border-box",
            }}
          >
            <h3 id="problem-mistake-title" style={{ fontSize: "1.125rem", fontWeight: 700, margin: "0 0 var(--space-3) 0" }}>
              Log Mistake for: {problem.title}
            </h3>

            {mistakeSuccess ? (
              <div style={{ color: "var(--status-success)", textAlign: "center", padding: "var(--space-4) 0" }}>
                ✓ Mistake logged successfully!
              </div>
            ) : (
              <form onSubmit={handleSaveMistake}>
                <div style={{ marginBottom: "var(--space-3)" }}>
                  <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, marginBottom: "4px" }}>
                    Category
                  </label>
                  <select
                    value={mistakeType}
                    onChange={(e) => setMistakeType(e.target.value as MistakeType)}
                    style={{
                      width: "100%",
                      padding: "var(--space-2)",
                      backgroundColor: "var(--bg-primary)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-md)",
                      color: "var(--text-primary)",
                    }}
                  >
                    <option value="CONCEPT_GAP">Concept Gap</option>
                    <option value="LOGIC_ERROR">Logic Error</option>
                    <option value="EDGE_CASE">Edge Case Missed</option>
                    <option value="COMPLEXITY_ISSUE">Complexity Issue</option>
                    <option value="SYNTAX_ERROR">Syntax Error</option>
                    <option value="IMPLEMENTATION_ERROR">Implementation Error</option>
                    <option value="MISUNDERSTANDING">Misunderstanding</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>

                <div style={{ marginBottom: "var(--space-3)" }}>
                  <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, marginBottom: "4px" }}>
                    Summary / Title *
                  </label>
                  <input
                    type="text"
                    required
                    value={mistakeTitle}
                    onChange={(e) => setMistakeTitle(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "var(--space-2)",
                      backgroundColor: "var(--bg-primary)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-md)",
                      color: "var(--text-primary)",
                      boxSizing: "border-box",
                    }}
                  />
                </div>

                <div style={{ marginBottom: "var(--space-3)" }}>
                  <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, marginBottom: "4px" }}>
                    What tripped you up? *
                  </label>
                  <textarea
                    required
                    rows={3}
                    value={mistakeDesc}
                    onChange={(e) => setMistakeDesc(e.target.value)}
                    placeholder="e.g. Forgot to handle empty array base case..."
                    style={{
                      width: "100%",
                      padding: "var(--space-2)",
                      backgroundColor: "var(--bg-primary)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-md)",
                      color: "var(--text-primary)",
                      boxSizing: "border-box",
                    }}
                  />
                </div>

                <div style={{ marginBottom: "var(--space-4)" }}>
                  <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, marginBottom: "4px" }}>
                    Takeaway / Correct Approach
                  </label>
                  <textarea
                    rows={2}
                    value={mistakeCorrection}
                    onChange={(e) => setMistakeCorrection(e.target.value)}
                    placeholder="Check len(arr) == 0 before dereferencing head..."
                    style={{
                      width: "100%",
                      padding: "var(--space-2)",
                      backgroundColor: "var(--bg-primary)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-md)",
                      color: "var(--text-primary)",
                      boxSizing: "border-box",
                    }}
                  />
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: "var(--space-2)" }}>
                  <button
                    type="button"
                    onClick={() => setShowMistakeModal(false)}
                    style={{
                      background: "none",
                      border: "1px solid var(--border-subtle)",
                      color: "var(--text-secondary)",
                      padding: "var(--space-2) var(--space-4)",
                      borderRadius: "var(--radius-md)",
                      cursor: "pointer",
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={mistakeSubmitting}
                    style={{
                      backgroundColor: "var(--brand-primary)",
                      color: "#ffffff",
                      border: "none",
                      padding: "var(--space-2) var(--space-5)",
                      borderRadius: "var(--radius-md)",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    {mistakeSubmitting ? "Saving..." : "Save Mistake"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </main>
  );
};
