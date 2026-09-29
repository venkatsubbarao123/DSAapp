import React, { useEffect, useState } from "react";
import { fetchApi } from "../services/apiClient.ts";
import { useAuth } from "../context/AuthContext.tsx";
import { SubmissionDetail } from "../types/progress.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";

interface SubmissionDetailPageProps {
  submissionId: string;
  onNavigate: (path: string) => void;
}

export const SubmissionDetailPage: React.FC<SubmissionDetailPageProps> = ({
  submissionId,
  onNavigate,
}) => {
  const { isAuthenticated, openAuthModal } = useAuth();
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchApi<SubmissionDetail>(`/api/v1/submissions/${submissionId}`)
      .then((res) => {
        if (isMounted) setSubmission(res.data);
      })
      .catch((err: unknown) => {
        if (!isMounted) return;
        const msg = err instanceof Error ? err.message : "Failed to load submission details.";
        setError(msg);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [submissionId, isAuthenticated]);

  const copyToClipboard = () => {
    if (!submission?.source_code) return;
    navigator.clipboard.writeText(submission.source_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isAuthenticated) {
    return (
      <main id="main-content" style={{ flex: 1, padding: "var(--space-12) var(--space-6)", textAlign: "center" }}>
        <button
          onClick={() => openAuthModal("login")}
          style={{
            backgroundColor: "var(--brand-primary)",
            color: "#ffffff",
            border: "none",
            padding: "var(--space-3) var(--space-6)",
            borderRadius: "var(--radius-md)",
            cursor: "pointer",
          }}
        >
          Sign in to view this submission
        </button>
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

  if (error || !submission) {
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
          {error || "Submission record not found or inaccessible."}
        </div>
        <button
          onClick={() => onNavigate("/submissions")}
          style={{
            background: "none",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-primary)",
            padding: "var(--space-2) var(--space-4)",
            borderRadius: "var(--radius-md)",
            cursor: "pointer",
          }}
        >
          ← Return to Submissions
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
      <div style={{ display: "flex", gap: "var(--space-4)", marginBottom: "var(--space-6)" }}>
        <button
          onClick={() => onNavigate("/submissions")}
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
          ← Back to Submissions
        </button>
        <span style={{ color: "var(--text-muted)" }}>•</span>
        <button
          onClick={() => onNavigate(`/problems/${submission.problem_slug}`)}
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
          Go to Problem Statement →
        </button>
      </div>

      {/* Header Info */}
      <header
        style={{
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-lg)",
          padding: "var(--space-5) var(--space-6)",
          marginBottom: "var(--space-6)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "var(--space-4)" }}>
          <div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
              ID: {submission.public_id}
            </span>
            <h1 style={{ fontSize: "1.5rem", fontWeight: 800, margin: "4px 0 var(--space-2) 0" }}>
              {submission.problem_title}
            </h1>
            <div style={{ display: "flex", gap: "var(--space-3)", alignItems: "center", fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
              <span>Language: <strong style={{ color: "var(--text-primary)" }}>{submission.language}</strong></span>
              <span>•</span>
              <span>Submitted: {new Date(submission.created_at).toLocaleString()}</span>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "var(--space-2)" }}>
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 700,
                padding: "3px 10px",
                borderRadius: "var(--radius-full)",
                backgroundColor: "rgba(59, 130, 246, 0.15)",
                color: "var(--brand-primary)",
                border: "1px solid rgba(59, 130, 246, 0.3)",
              }}
            >
              {submission.status.replace(/_/g, " ")}
            </span>
            <button
              onClick={copyToClipboard}
              style={{
                background: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-primary)",
                padding: "4px 10px",
                borderRadius: "var(--radius-md)",
                fontSize: "0.75rem",
                cursor: "pointer",
              }}
            >
              {copied ? "Copied!" : "Copy Code"}
            </button>
          </div>
        </div>
      </header>

      {/* Execution Verdict & Metrics Card */}
      {submission.result && (
        <section
          role="region"
          aria-label="Judge Execution Result"
          style={{
            backgroundColor:
              submission.result.verdict === "ACCEPTED"
                ? "rgba(35, 134, 54, 0.15)"
                : "rgba(218, 54, 51, 0.15)",
            border: `1px solid ${
              submission.result.verdict === "ACCEPTED" ? "#238636" : "#da3633"
            }`,
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-5) var(--space-6)",
            marginBottom: "var(--space-6)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
            <h2
              style={{
                margin: 0,
                fontSize: "1.125rem",
                fontWeight: 700,
                color: submission.result.verdict === "ACCEPTED" ? "#3fb950" : "#f85149",
              }}
            >
              {submission.result.verdict === "ACCEPTED" ? "✓ Accepted" : `✗ ${submission.result.verdict.replace(/_/g, " ")}`}
            </h2>
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 700,
                padding: "3px 10px",
                borderRadius: "var(--radius-full)",
                backgroundColor:
                  submission.result.verdict === "ACCEPTED"
                    ? "rgba(35, 134, 54, 0.3)"
                    : "rgba(218, 54, 51, 0.3)",
                color: "#ffffff",
              }}
            >
              {submission.result.verdict}
            </span>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
              gap: "var(--space-3)",
              marginBottom: "var(--space-3)",
              padding: "var(--space-3)",
              backgroundColor: "rgba(0, 0, 0, 0.2)",
              borderRadius: "var(--radius-sm)",
            }}
          >
            <div>
              <span style={{ color: "var(--text-secondary)", fontSize: "0.75rem", display: "block" }}>Test Cases</span>
              <strong style={{ fontSize: "1rem", color: "var(--text-primary)" }}>
                {submission.result.tests_passed} / {submission.result.tests_total}
              </strong>
            </div>
            <div>
              <span style={{ color: "var(--text-secondary)", fontSize: "0.75rem", display: "block" }}>Runtime</span>
              <strong style={{ fontSize: "1rem", color: "var(--text-primary)" }}>
                {submission.result.execution_time_ms ?? 0} ms
              </strong>
            </div>
            <div>
              <span style={{ color: "var(--text-secondary)", fontSize: "0.75rem", display: "block" }}>Memory</span>
              <strong style={{ fontSize: "1rem", color: "var(--text-primary)" }}>
                {Math.round((submission.result.memory_used_bytes ?? 0) / (1024 * 1024))} MB
              </strong>
            </div>
          </div>

          {(submission.result.compiler_output_safe || submission.result.runtime_output_safe) && (
            <div style={{ marginTop: "var(--space-3)" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                Compiler / Runtime Log:
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
                {submission.result.compiler_output_safe || submission.result.runtime_output_safe}
              </pre>
            </div>
          )}
        </section>
      )}

      {/* Execution Notice Box */}
      {submission.execution_notice && (
        <div
          style={{
            border: "1px dashed var(--border-muted)",
            borderRadius: "var(--radius-md)",
            padding: "var(--space-3) var(--space-5)",
            marginBottom: "var(--space-6)",
            fontSize: "0.8125rem",
            color: "var(--text-muted)",
            backgroundColor: "var(--bg-tertiary)",
          }}
        >
          <strong>Notice:</strong> {submission.execution_notice}
        </div>
      )}

      {/* Source Code Container (Safe string rendering) */}
      <section>
        <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "var(--space-2)" }}>
          Submitted Source Code
        </h2>
        <div
          style={{
            backgroundColor: "#0d1117",
            borderRadius: "var(--radius-lg)",
            border: "1px solid #30363d",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "var(--space-2) var(--space-4)",
              backgroundColor: "#161b22",
              borderBottom: "1px solid #30363d",
              fontSize: "0.75rem",
              fontFamily: "var(--font-mono)",
              color: "#8b949e",
              display: "flex",
              justifyContent: "space-between",
            }}
          >
            <span>{submission.language}</span>
            <span>{new Blob([submission.source_code]).size} bytes</span>
          </div>
          <pre
            style={{
              margin: 0,
              padding: "var(--space-4) var(--space-6)",
              fontFamily: "var(--font-mono)",
              fontSize: "0.875rem",
              lineHeight: 1.6,
              color: "#c9d1d9",
              overflowX: "auto",
              whiteSpace: "pre",
            }}
          >
            <code>{submission.source_code}</code>
          </pre>
        </div>
      </section>
    </main>
  );
};
