import React, { useState, useEffect } from "react";
import { fetchApi, APIClientError } from "../services/apiClient.ts";
import { useAuth } from "../context/AuthContext.tsx";
import { ProblemDetail, ProblemDifficulty } from "../types/curriculum.ts";
import {
  ProblemProgress,
  SubmissionDetail,
  SubmissionResult,
  SubmissionStatus,
  MistakeType,
  RunCodeResult,
} from "../types/progress.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";
import { PremiumGate } from "../components/common/PremiumGate.tsx";

interface ProblemDetailPageProps {
  problemId: string;
  onNavigate: (path: string) => void;
}

const DEFAULT_STARTER_CODE: Record<string, string> = {
  python: `# Solution in Python 3
# Read input from standard input and print output to standard output
import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    # Process data and print result
    # Example: nums = [int(x) for x in data]
    # print(result)

if __name__ == "__main__":
    solve()
`,
  javascript: `// Solution in JavaScript (Node.js)
const fs = require('fs');

function solve() {
  const input = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/);
  if (!input || input[0] === '') return;
  // Process input and output with console.log
}

solve();
`,
  typescript: `// Solution in TypeScript
import * as fs from 'fs';

function solve(): void {
  const input = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/);
  if (!input || input[0] === '') return;
  // Process input and output with console.log
}

solve();
`,
  java: `// Solution in Java 17
import java.util.Scanner;

public class Solution {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (!sc.hasNext()) return;
        // Read input with sc and print with System.out.println
    }
}
`,
  cpp: `// Solution in C++20
#include <iostream>
#include <vector>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    // Read with cin, write with cout
    return 0;
}
`,
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
  const [solutionRevealed, setSolutionRevealed] = useState(false);
  const [showSolutionModal, setShowSolutionModal] = useState(false);

  // Code & Editor State
  const [language, setLanguage] = useState<string>("python");
  const [sourceCode, setSourceCode] = useState<string>(DEFAULT_STARTER_CODE.python);

  // Run State
  const [isRunning, setIsRunning] = useState(false);
  const [runResult, setRunResult] = useState<RunCodeResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [activeConsoleTab, setActiveConsoleTab] = useState<"testcase" | "run" | "submission">("testcase");
  const [selectedCaseIdx, setSelectedCaseIdx] = useState(0);
  const [useCustomInput, setUseCustomInput] = useState(false);
  const [customInput, setCustomInput] = useState("");

  // Submission State
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

  const handleResetCode = () => {
    if (window.confirm("Reset code to default starter template? Your current changes will be discarded.")) {
      setSourceCode(DEFAULT_STARTER_CODE[language] || "");
    }
  };

  const handleRunCode = async () => {
    if (!isAuthenticated) {
      openAuthModal("login");
      return;
    }
    if (!problem) return;

    const utf8Bytes = new TextEncoder().encode(sourceCode);
    if (utf8Bytes.length > 65536) {
      setRunError("Source code exceeds maximum allowed size of 64KB.");
      return;
    }

    setIsRunning(true);
    setRunError(null);
    setActiveConsoleTab("run");

    try {
      const res = await fetchApi<RunCodeResult>(`/api/v1/problems/${problem.id}/run`, {
        method: "POST",
        body: JSON.stringify({
          language,
          source_code: sourceCode,
          custom_input: useCustomInput ? customInput : null,
        }),
      });
      setRunResult(res.data);
      setSelectedCaseIdx(0);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to run code in sandbox.";
      setRunError(msg);
    } finally {
      setIsRunning(false);
    }
  };

  const handleSubmitCode = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
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
    setJudgingStatus("QUEUED");
    setSubmissionResult(null);
    setActiveConsoleTab("submission");

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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-6)", flexWrap: "wrap", gap: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button
            onClick={() => onNavigate("/")}
            style={{
              background: "none",
              border: "none",
              color: "var(--text-secondary)",
              fontWeight: 500,
              fontSize: "0.875rem",
              cursor: "pointer",
              padding: 0,
            }}
          >
            🏠 Home
          </button>
          <span style={{ color: "var(--border-muted)" }}>/</span>
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
            ← Problems
          </button>
        </div>

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
          {isAuthenticated && progress ? (
            <div style={{ display: "inline-flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
              {progress.status === "SOLVED" && (
                <span
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    padding: "3px 8px",
                    borderRadius: "var(--radius-sm, 4px)",
                    backgroundColor: "#dcfce7",
                    color: "#15803d",
                    border: "1px solid #86efac",
                  }}
                >
                  ✓ Completed
                </span>
              )}
              <span
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  padding: "3px 10px",
                  borderRadius: "var(--radius-full, 9999px)",
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
            </div>
          ) : (
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                padding: "3px 8px",
                borderRadius: "var(--radius-sm, 4px)",
                backgroundColor: "var(--bg-tertiary)",
                color: "var(--text-muted)",
              }}
            >
              👥 Solved by 150+ learners
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

      {/* Official Solution & Editorial Section */}
      <section style={{ marginBottom: "var(--space-8)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>
            Official Solution & Editorial
          </h2>
          {!solutionRevealed && (
            <button
              onClick={() => setShowSolutionModal(true)}
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                padding: "6px 14px",
                fontSize: "0.8125rem",
                fontWeight: 600,
                color: "var(--brand-primary)",
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              <span>👁</span> View Solution
            </button>
          )}
        </div>

        {solutionRevealed ? (
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-6)",
            }}
          >
            <div style={{ display: "flex", gap: "var(--space-4)", marginBottom: "var(--space-4)", flexWrap: "wrap" }}>
              <div style={{ backgroundColor: "var(--bg-tertiary)", padding: "6px 12px", borderRadius: "var(--radius-sm)", fontSize: "0.8125rem" }}>
                <span style={{ color: "var(--text-muted)" }}>Time Complexity: </span>
                <strong style={{ color: "var(--brand-primary)", fontFamily: "var(--font-mono)" }}>
                  {problem.expected_time_complexity || "O(n)"}
                </strong>
              </div>
              <div style={{ backgroundColor: "var(--bg-tertiary)", padding: "6px 12px", borderRadius: "var(--radius-sm)", fontSize: "0.8125rem" }}>
                <span style={{ color: "var(--text-muted)" }}>Space Complexity: </span>
                <strong style={{ color: "var(--brand-primary)", fontFamily: "var(--font-mono)" }}>
                  {problem.expected_space_complexity || "O(1)"}
                </strong>
              </div>
            </div>

            <h4 style={{ fontSize: "0.9375rem", fontWeight: 700, marginBottom: "var(--space-2)" }}>
              Algorithmic Approach & Key Insights:
            </h4>
            <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
              {problem.explanation || "Apply optimal algorithmic design pattern. Break down into base cases, state transitions or two-pointer passes to reach target complexity without excessive space allocation."}
            </div>
          </div>
        ) : (
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px dashed var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-6)",
              textAlign: "center",
              color: "var(--text-muted)",
              fontSize: "0.875rem",
            }}
          >
            Official solution is hidden to encourage independent problem solving. Click &quot;View Solution&quot; to reveal complexity analysis and reference approach.
          </div>
        )}
      </section>
      <section style={{ marginBottom: "var(--space-8)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>
            Submit Solution Code
          </h2>
          <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            ⚡ Docker Sandbox Active
          </span>
        </div>

        {/* Editor Box */}
        <div
          style={{
            backgroundColor: "#161b22",
            border: "1px solid #30363d",
            borderRadius: "var(--radius-lg)",
            overflow: "hidden",
            boxShadow: "var(--shadow-md)",
          }}
        >
          {/* Editor Header Bar */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "var(--space-2) var(--space-4)",
              backgroundColor: "#0d1117",
              borderBottom: "1px solid #30363d",
              flexWrap: "wrap",
              gap: "var(--space-2)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
              <label style={{ fontSize: "0.75rem", color: "#8b949e", fontWeight: 600 }}>Language:</label>
              <select
                value={language}
                onChange={(e) => handleLanguageChange(e.target.value)}
                style={{
                  backgroundColor: "#21262d",
                  color: "#c9d1d9",
                  border: "1px solid #30363d",
                  borderRadius: "var(--radius-sm)",
                  padding: "4px 10px",
                  fontSize: "0.8125rem",
                  cursor: "pointer",
                }}
                aria-label="Select programming language"
              >
                <option value="python">Python 3.12</option>
                <option value="javascript">JavaScript (Node.js 20)</option>
                <option value="typescript">TypeScript 5.x</option>
                <option value="java">Java 17 (OpenJDK)</option>
                <option value="cpp">C++20 (GCC 13)</option>
              </select>

              <button
                type="button"
                onClick={handleResetCode}
                style={{
                  background: "none",
                  border: "none",
                  color: "#8b949e",
                  fontSize: "0.75rem",
                  cursor: "pointer",
                  textDecoration: "underline",
                }}
                title="Reset to default starter template"
              >
                Reset Code
              </button>
            </div>

            <span style={{ fontSize: "0.75rem", color: "#8b949e", fontFamily: "var(--font-mono)" }}>
              {new TextEncoder().encode(sourceCode).length} / 65536 bytes
            </span>
          </div>

          {/* Textarea Code Editor */}
          <textarea
            value={sourceCode}
            onChange={(e) => setSourceCode(e.target.value)}
            rows={14}
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
            placeholder="Write your solution here..."
            aria-label="Code editor"
          />

          {/* Action Toolbar */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "var(--space-3) var(--space-4)",
              backgroundColor: "#161b22",
              borderTop: "1px solid #30363d",
              flexWrap: "wrap",
              gap: "var(--space-3)",
            }}
          >
            {/* Console Tab Switches */}
            <div style={{ display: "flex", gap: "var(--space-2)" }}>
              <button
                type="button"
                onClick={() => setActiveConsoleTab("testcase")}
                style={{
                  backgroundColor: activeConsoleTab === "testcase" ? "#21262d" : "transparent",
                  color: activeConsoleTab === "testcase" ? "#ffffff" : "#8b949e",
                  border: activeConsoleTab === "testcase" ? "1px solid #30363d" : "1px solid transparent",
                  borderRadius: "var(--radius-sm)",
                  padding: "4px 10px",
                  fontSize: "0.8125rem",
                  cursor: "pointer",
                  fontWeight: 600,
                }}
              >
                📋 Testcases
              </button>
              <button
                type="button"
                onClick={() => setActiveConsoleTab("run")}
                style={{
                  backgroundColor: activeConsoleTab === "run" ? "#21262d" : "transparent",
                  color: activeConsoleTab === "run" ? "#ffffff" : "#8b949e",
                  border: activeConsoleTab === "run" ? "1px solid #30363d" : "1px solid transparent",
                  borderRadius: "var(--radius-sm)",
                  padding: "4px 10px",
                  fontSize: "0.8125rem",
                  cursor: "pointer",
                  fontWeight: 600,
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <span>💻 Run Output</span>
                {runResult && (
                  <span
                    style={{
                      display: "inline-block",
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      backgroundColor: runResult.all_passed ? "var(--status-success)" : "var(--status-danger)",
                    }}
                  />
                )}
              </button>
              <button
                type="button"
                onClick={() => setActiveConsoleTab("submission")}
                style={{
                  backgroundColor: activeConsoleTab === "submission" ? "#21262d" : "transparent",
                  color: activeConsoleTab === "submission" ? "#ffffff" : "#8b949e",
                  border: activeConsoleTab === "submission" ? "1px solid #30363d" : "1px solid transparent",
                  borderRadius: "var(--radius-sm)",
                  padding: "4px 10px",
                  fontSize: "0.8125rem",
                  cursor: "pointer",
                  fontWeight: 600,
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <span>🏆 Submission Result</span>
                {submissionResult && (
                  <span
                    style={{
                      display: "inline-block",
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      backgroundColor: submissionResult.verdict === "ACCEPTED" ? "var(--status-success)" : "var(--status-danger)",
                    }}
                  />
                )}
              </button>
            </div>

            {/* Run and Submit Action Buttons */}
            <div style={{ display: "flex", gap: "var(--space-3)" }}>
              <button
                type="button"
                onClick={handleRunCode}
                disabled={isRunning || submitting}
                style={{
                  backgroundColor: "#21262d",
                  color: "#c9d1d9",
                  border: "1px solid #30363d",
                  padding: "var(--space-2) var(--space-4)",
                  borderRadius: "var(--radius-md)",
                  fontWeight: 600,
                  cursor: isRunning || submitting ? "not-allowed" : "pointer",
                  fontSize: "0.875rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  opacity: isRunning || submitting ? 0.6 : 1,
                }}
              >
                {isRunning ? "⏳ Running..." : "▶ Run Sample Code"}
              </button>

              <button
                type="button"
                onClick={() => handleSubmitCode()}
                disabled={submitting || isRunning}
                style={{
                  backgroundColor: "var(--brand-primary)",
                  color: "#ffffff",
                  border: "none",
                  padding: "var(--space-2) var(--space-5)",
                  borderRadius: "var(--radius-md)",
                  fontWeight: 600,
                  cursor: submitting || isRunning ? "not-allowed" : "pointer",
                  fontSize: "0.875rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  opacity: submitting || isRunning ? 0.6 : 1,
                }}
              >
                {submitting || isPolling ? "⏳ Judging..." : "Submit Code (Queue for Judge)"}
              </button>
            </div>
          </div>
        </div>

        {/* Console / Output Panel */}
        <div
          style={{
            marginTop: "var(--space-4)",
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-4)",
            minHeight: "160px",
          }}
        >
          {/* TAB 1: TESTCASES */}
          {activeConsoleTab === "testcase" && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)", flexWrap: "wrap", gap: "var(--space-2)" }}>
                <div style={{ display: "flex", gap: "var(--space-2)" }}>
                  {problem.sample_test_cases?.map((tc, idx) => (
                    <button
                      key={tc.id || idx}
                      type="button"
                      onClick={() => {
                        setSelectedCaseIdx(idx);
                        setUseCustomInput(false);
                      }}
                      style={{
                        backgroundColor: !useCustomInput && selectedCaseIdx === idx ? "var(--brand-primary)" : "var(--bg-tertiary)",
                        color: !useCustomInput && selectedCaseIdx === idx ? "#ffffff" : "var(--text-primary)",
                        border: "1px solid var(--border-subtle)",
                        borderRadius: "var(--radius-sm)",
                        padding: "4px 12px",
                        fontSize: "0.8125rem",
                        cursor: "pointer",
                        fontWeight: 600,
                      }}
                    >
                      Case {idx + 1}
                    </button>
                  ))}
                  <button
                    type="button"
                    onClick={() => setUseCustomInput(!useCustomInput)}
                    style={{
                      backgroundColor: useCustomInput ? "var(--brand-primary)" : "var(--bg-tertiary)",
                      color: useCustomInput ? "#ffffff" : "var(--text-primary)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-sm)",
                      padding: "4px 12px",
                      fontSize: "0.8125rem",
                      cursor: "pointer",
                      fontWeight: 600,
                    }}
                  >
                    Custom Stdin ✍️
                  </button>
                </div>
              </div>

              {useCustomInput ? (
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                    Standard Input (stdin):
                  </span>
                  <textarea
                    value={customInput}
                    onChange={(e) => setCustomInput(e.target.value)}
                    rows={4}
                    placeholder="Enter custom input to pass into stdin..."
                    style={{
                      width: "100%",
                      backgroundColor: "#0d1117",
                      color: "#c9d1d9",
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.8125rem",
                      padding: "var(--space-3)",
                      borderRadius: "var(--radius-sm)",
                      border: "1px solid var(--border-subtle)",
                      boxSizing: "border-box",
                    }}
                  />
                </div>
              ) : (
                problem.sample_test_cases && problem.sample_test_cases[selectedCaseIdx] && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
                    <div>
                      <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                        Input:
                      </span>
                      <pre
                        style={{
                          margin: 0,
                          backgroundColor: "#0d1117",
                          color: "#c9d1d9",
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.8125rem",
                          padding: "var(--space-3)",
                          borderRadius: "var(--radius-sm)",
                          border: "1px solid var(--border-subtle)",
                          whiteSpace: "pre-wrap",
                        }}
                      >
                        {problem.sample_test_cases[selectedCaseIdx].input}
                      </pre>
                    </div>
                    <div>
                      <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                        Expected Output:
                      </span>
                      <pre
                        style={{
                          margin: 0,
                          backgroundColor: "#0d1117",
                          color: "#3fb950",
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.8125rem",
                          padding: "var(--space-3)",
                          borderRadius: "var(--radius-sm)",
                          border: "1px solid var(--border-subtle)",
                          whiteSpace: "pre-wrap",
                        }}
                      >
                        {problem.sample_test_cases[selectedCaseIdx].expected_output}
                      </pre>
                    </div>
                  </div>
                )
              )}
            </div>
          )}

          {/* TAB 2: RUN OUTPUT */}
          {activeConsoleTab === "run" && (
            <div>
              {isRunning ? (
                <div style={{ textAlign: "center", padding: "var(--space-8)" }}>
                  <LoadingSpinner />
                  <p style={{ marginTop: "var(--space-3)", fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                    Executing code against sample cases in Docker container...
                  </p>
                </div>
              ) : runError ? (
                <div
                  style={{
                    backgroundColor: "var(--status-danger-bg)",
                    border: "1px solid var(--status-danger)",
                    color: "var(--status-danger)",
                    padding: "var(--space-3) var(--space-4)",
                    borderRadius: "var(--radius-md)",
                    fontSize: "0.875rem",
                  }}
                >
                  <strong>Execution Error:</strong> {runError}
                </div>
              ) : runResult ? (
                <div>
                  {/* Status Banner */}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      paddingBottom: "var(--space-3)",
                      borderBottom: "1px solid var(--border-subtle)",
                      marginBottom: "var(--space-4)",
                      flexWrap: "wrap",
                      gap: "var(--space-2)",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
                      <span
                        style={{
                          fontSize: "1.125rem",
                          fontWeight: 700,
                          color: runResult.all_passed ? "#3fb950" : "#f85149",
                        }}
                      >
                        {runResult.status === "ACCEPTED" ? "✓ Accepted (Sample Tests)" : `✗ ${runResult.status.replace(/_/g, " ")}`}
                      </span>
                      <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                        {runResult.passed_count} / {runResult.total_count} sample testcases passed
                      </span>
                    </div>

                    <div style={{ display: "flex", gap: "var(--space-4)", fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                      <span>Runtime: <strong style={{ color: "var(--text-primary)" }}>{runResult.peak_runtime_ms} ms</strong></span>
                      <span>Memory: <strong style={{ color: "var(--text-primary)" }}>{Math.round(runResult.peak_memory_bytes / (1024 * 1024))} MB</strong></span>
                    </div>
                  </div>

                  {/* Compiler error display if any */}
                  {runResult.compiler_output && (
                    <div style={{ marginBottom: "var(--space-4)" }}>
                      <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "#f85149", display: "block", marginBottom: "4px" }}>
                        Compilation Error:
                      </span>
                      <pre
                        style={{
                          backgroundColor: "#0d1117",
                          color: "#f85149",
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.8125rem",
                          padding: "var(--space-3)",
                          borderRadius: "var(--radius-sm)",
                          border: "1px solid #da3633",
                          whiteSpace: "pre-wrap",
                          overflowX: "auto",
                        }}
                      >
                        {runResult.compiler_output}
                      </pre>
                    </div>
                  )}

                  {/* Testcase selector tabs */}
                  {runResult.test_cases && runResult.test_cases.length > 0 && (
                    <>
                      <div style={{ display: "flex", gap: "var(--space-2)", marginBottom: "var(--space-3)" }}>
                        {runResult.test_cases.map((tc, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => setSelectedCaseIdx(idx)}
                            style={{
                              backgroundColor: selectedCaseIdx === idx ? "#21262d" : "var(--bg-tertiary)",
                              color: tc.passed ? "#3fb950" : "#f85149",
                              border: selectedCaseIdx === idx ? "1px solid #30363d" : "1px solid var(--border-subtle)",
                              borderRadius: "var(--radius-sm)",
                              padding: "4px 12px",
                              fontSize: "0.8125rem",
                              cursor: "pointer",
                              fontWeight: 600,
                              display: "flex",
                              alignItems: "center",
                              gap: "6px",
                            }}
                          >
                            <span>{tc.passed ? "✓" : "✗"}</span>
                            <span>Case {tc.case_number}</span>
                          </button>
                        ))}
                      </div>

                      {/* Details of selected case */}
                      {runResult.test_cases[selectedCaseIdx] && (
                        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
                          <div>
                            <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                              Input:
                            </span>
                            <pre
                              style={{
                                margin: 0,
                                backgroundColor: "#0d1117",
                                color: "#c9d1d9",
                                fontFamily: "var(--font-mono)",
                                fontSize: "0.8125rem",
                                padding: "var(--space-3)",
                                borderRadius: "var(--radius-sm)",
                                border: "1px solid var(--border-subtle)",
                                whiteSpace: "pre-wrap",
                              }}
                            >
                              {runResult.test_cases[selectedCaseIdx].input}
                            </pre>
                          </div>

                          {runResult.test_cases[selectedCaseIdx].expected_output && (
                            <div>
                              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                                Expected Output:
                              </span>
                              <pre
                                style={{
                                  margin: 0,
                                  backgroundColor: "#0d1117",
                                  color: "#3fb950",
                                  fontFamily: "var(--font-mono)",
                                  fontSize: "0.8125rem",
                                  padding: "var(--space-3)",
                                  borderRadius: "var(--radius-sm)",
                                  border: "1px solid var(--border-subtle)",
                                  whiteSpace: "pre-wrap",
                                }}
                              >
                                {runResult.test_cases[selectedCaseIdx].expected_output}
                              </pre>
                            </div>
                          )}

                          <div>
                            <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                              Your Output:
                            </span>
                            <pre
                              style={{
                                margin: 0,
                                backgroundColor: "#0d1117",
                                color: runResult.test_cases[selectedCaseIdx].passed ? "#3fb950" : "#f85149",
                                fontFamily: "var(--font-mono)",
                                fontSize: "0.8125rem",
                                padding: "var(--space-3)",
                                borderRadius: "var(--radius-sm)",
                                border: `1px solid ${runResult.test_cases[selectedCaseIdx].passed ? "#238636" : "#da3633"}`,
                                whiteSpace: "pre-wrap",
                              }}
                            >
                              {runResult.test_cases[selectedCaseIdx].actual_output || "<No stdout output produced>"}
                            </pre>
                          </div>

                          {runResult.test_cases[selectedCaseIdx].stderr && (
                            <div>
                              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "#f85149", display: "block", marginBottom: "4px" }}>
                                Stderr / Error Output:
                              </span>
                              <pre
                                style={{
                                  margin: 0,
                                  backgroundColor: "#0d1117",
                                  color: "#f85149",
                                  fontFamily: "var(--font-mono)",
                                  fontSize: "0.75rem",
                                  padding: "var(--space-3)",
                                  borderRadius: "var(--radius-sm)",
                                  border: "1px solid #da3633",
                                  whiteSpace: "pre-wrap",
                                }}
                              >
                                {runResult.test_cases[selectedCaseIdx].stderr}
                              </pre>
                            </div>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </div>
              ) : (
                <div style={{ textAlign: "center", padding: "var(--space-6)", color: "var(--text-muted)" }}>
                  Click <strong>▶ Run Sample Code</strong> above to execute your solution against sample testcases.
                </div>
              )}
            </div>
          )}

          {/* TAB 3: SUBMISSION RESULT */}
          {activeConsoleTab === "submission" && (
            <div>
              {submitting ? (
                <div style={{ textAlign: "center", padding: "var(--space-8)" }}>
                  <LoadingSpinner />
                  <p style={{ marginTop: "var(--space-3)", fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                    Submitting solution to judge...
                  </p>
                </div>
              ) : submissionError ? (
                <div
                  style={{
                    backgroundColor: "var(--status-danger-bg)",
                    border: "1px solid var(--status-danger)",
                    color: "var(--status-danger)",
                    padding: "var(--space-3) var(--space-4)",
                    borderRadius: "var(--radius-md)",
                    fontSize: "0.875rem",
                  }}
                >
                  <strong>Submission Error:</strong> {submissionError}
                </div>
              ) : submissionFeedback ? (
                <div>
                  {/* Verdict Banner */}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "var(--space-4)",
                      borderRadius: "var(--radius-md)",
                      backgroundColor:
                        submissionResult?.verdict === "ACCEPTED"
                          ? "rgba(35, 134, 54, 0.15)"
                          : submissionResult?.verdict
                          ? "rgba(218, 54, 51, 0.15)"
                          : "rgba(5, 150, 105, 0.1)",
                      border: `1px solid ${
                        submissionResult?.verdict === "ACCEPTED"
                          ? "#238636"
                          : submissionResult?.verdict
                          ? "#da3633"
                          : "var(--status-success)"
                      }`,
                      marginBottom: "var(--space-4)",
                    }}
                  >
                    <div>
                      <div
                        style={{
                          fontSize: "1.25rem",
                          fontWeight: 700,
                          color:
                            submissionResult?.verdict === "ACCEPTED"
                              ? "#3fb950"
                              : submissionResult?.verdict
                              ? "#f85149"
                              : "var(--status-success)",
                        }}
                      >
                        {submissionResult
                          ? submissionResult.verdict === "ACCEPTED"
                            ? "✓ Accepted"
                            : `✗ ${submissionResult.verdict.replace(/_/g, " ")}`
                          : "✓ Submission Received & Queued!"}
                      </div>
                      <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                        ID: <span style={{ fontFamily: "var(--font-mono)" }}>{submissionFeedback.public_id}</span>
                      </div>
                    </div>

                    <span
                      style={{
                        fontSize: "0.8125rem",
                        fontWeight: 700,
                        padding: "4px 12px",
                        borderRadius: "var(--radius-full)",
                        backgroundColor:
                          submissionResult?.verdict === "ACCEPTED"
                            ? "rgba(35, 134, 54, 0.3)"
                            : "rgba(255, 255, 255, 0.1)",
                        color:
                          submissionResult?.verdict === "ACCEPTED"
                            ? "#3fb950"
                            : "var(--text-primary)",
                      }}
                    >
                      {judgingStatus || submissionFeedback.status}
                    </span>
                  </div>

                  {isPolling && !submissionResult && (
                    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", padding: "var(--space-3) var(--space-4)", marginBottom: "var(--space-4)", backgroundColor: "var(--bg-tertiary)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                      <LoadingSpinner />
                      <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                        Evaluating test cases in Docker sandbox...
                      </span>
                    </div>
                  )}

                  {/* Stat Grid */}
                  {submissionResult && (
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                        gap: "var(--space-3)",
                        marginBottom: "var(--space-4)",
                      }}
                    >
                      <div
                        style={{
                          backgroundColor: "var(--bg-tertiary)",
                          border: "1px solid var(--border-subtle)",
                          padding: "var(--space-3)",
                          borderRadius: "var(--radius-md)",
                        }}
                      >
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Test Cases</span>
                        <strong style={{ fontSize: "1.125rem", color: "var(--text-primary)" }}>
                          {submissionResult.tests_passed} / {submissionResult.tests_total}
                        </strong>
                      </div>

                      <div
                        style={{
                          backgroundColor: "var(--bg-tertiary)",
                          border: "1px solid var(--border-subtle)",
                          padding: "var(--space-3)",
                          borderRadius: "var(--radius-md)",
                        }}
                      >
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Runtime</span>
                        <strong style={{ fontSize: "1.125rem", color: "var(--text-primary)" }}>
                          {submissionResult.execution_time_ms ?? 0} ms
                        </strong>
                      </div>

                      <div
                        style={{
                          backgroundColor: "var(--bg-tertiary)",
                          border: "1px solid var(--border-subtle)",
                          padding: "var(--space-3)",
                          borderRadius: "var(--radius-md)",
                        }}
                      >
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Memory</span>
                        <strong style={{ fontSize: "1.125rem", color: "var(--text-primary)" }}>
                          {Math.round((submissionResult.memory_used_bytes ?? 0) / (1024 * 1024))} MB
                        </strong>
                      </div>
                    </div>
                  )}

                  {/* Logs & Error message */}
                  {(submissionResult?.compiler_output_safe || submissionResult?.runtime_output_safe) && (
                    <div style={{ marginBottom: "var(--space-4)" }}>
                      <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "#f85149", display: "block", marginBottom: "4px" }}>
                        Execution Output / Diagnostics:
                      </span>
                      <pre
                        style={{
                          backgroundColor: "#0d1117",
                          color: "#f85149",
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.8125rem",
                          padding: "var(--space-3)",
                          borderRadius: "var(--radius-sm)",
                          border: "1px solid #da3633",
                          whiteSpace: "pre-wrap",
                          maxHeight: "160px",
                          overflowY: "auto",
                        }}
                      >
                        {submissionResult.compiler_output_safe || submissionResult.runtime_output_safe}
                      </pre>
                    </div>
                  )}

                  {/* Actions */}
                  <div style={{ display: "flex", gap: "var(--space-4)", alignItems: "center", flexWrap: "wrap", marginTop: "var(--space-3)" }}>
                    <button
                      type="button"
                      onClick={() => onNavigate(`/submissions/${submissionFeedback.public_id}`)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "var(--brand-primary)",
                        fontWeight: 600,
                        cursor: "pointer",
                        fontSize: "0.875rem",
                        padding: 0,
                      }}
                    >
                      View in Submission History →
                    </button>

                    <button
                      type="button"
                      onClick={() => setShowMistakeModal(true)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "var(--text-secondary)",
                        cursor: "pointer",
                        fontSize: "0.875rem",
                        padding: 0,
                        textDecoration: "underline",
                      }}
                    >
                      📝 Log Mistake in Notebook
                    </button>

                    <button
                      type="button"
                      onClick={handleAddToRevision}
                      style={{
                        background: "none",
                        border: "none",
                        color: revisionAdded ? "var(--status-success)" : "var(--text-secondary)",
                        cursor: "pointer",
                        fontSize: "0.875rem",
                        padding: 0,
                        textDecoration: "underline",
                      }}
                    >
                      {revisionAdded ? "✓ Added to Revision!" : "🔄 Schedule for Spaced Revision"}
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: "center", padding: "var(--space-6)", color: "var(--text-muted)" }}>
                  Click <strong>🚀 Submit Code</strong> above to test your code against the complete test suite.
                </div>
              )}
            </div>
          )}
        </div>
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

      {/* View Solution Confirmation Modal */}
      {showSolutionModal && (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.65)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "var(--space-4)",
          }}
        >
          <div
            style={{
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              maxWidth: "480px",
              width: "100%",
              padding: "var(--space-6)",
              boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.3)",
            }}
          >
            <h3 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 var(--space-2) 0" }}>
              Reveal Solution Approach?
            </h3>
            <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.5, margin: "0 0 var(--space-6) 0" }}>
              Are you sure you want to reveal the solution? We recommend spending at least 15–20 minutes attempting the problem first or using progressive hints to build independent algorithmic problem-solving intuition.
            </p>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "var(--space-3)" }}>
              <button
                onClick={() => setShowSolutionModal(false)}
                style={{
                  backgroundColor: "var(--bg-tertiary)",
                  color: "var(--text-primary)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-md)",
                  padding: "8px 16px",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Keep Trying
              </button>
              <button
                onClick={() => {
                  setSolutionRevealed(true);
                  setShowSolutionModal(false);
                }}
                style={{
                  backgroundColor: "var(--brand-primary)",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "var(--radius-md)",
                  padding: "8px 16px",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Reveal Solution
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
};
