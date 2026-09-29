import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.tsx";
import { sqlApi } from "../services/sqlApi.ts";
import {
  SQLProblemSummary,
  SQLProblemDetail,
  SQLSubmissionResult,
} from "../types/sql.ts";

interface SqlPracticePageProps {
  onNavigate: (path: string) => void;
}

export const SqlPracticePage: React.FC<SqlPracticePageProps> = () => {
  const { isAuthenticated, openAuthModal } = useAuth();

  const [problems, setProblems] = useState<SQLProblemSummary[]>([]);
  const [selectedSlug, setSelectedSlug] = useState<string>("");
  const [problemDetail, setProblemDetail] = useState<SQLProblemDetail | null>(null);
  const [query, setQuery] = useState<string>("SELECT * FROM ");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [result, setResult] = useState<SQLSubmissionResult | null>(null);
  const [showHints, setShowHints] = useState<boolean>(false);
  const [loadingProbs, setLoadingProbs] = useState<boolean>(true);
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchProbs = async () => {
      setLoadingProbs(true);
      try {
        const list = await sqlApi.getProblems();
        setProblems(list);
        if (list.length > 0) {
          setSelectedSlug(list[0].slug);
        }
      } catch (err: unknown) {
        setErrorMsg(err instanceof Error ? err.message : "Failed to load SQL problems");
      } finally {
        setLoadingProbs(false);
      }
    };
    fetchProbs();
  }, []);

  useEffect(() => {
    if (!selectedSlug) return;
    const fetchDetail = async () => {
      setLoadingDetail(true);
      setResult(null);
      setShowHints(false);
      try {
        const detail = await sqlApi.getProblemDetail(selectedSlug);
        setProblemDetail(detail);
        if (detail.parsed_schemas && detail.parsed_schemas.length > 0) {
          setQuery(`SELECT * FROM ${detail.parsed_schemas[0].table_name} LIMIT 10;`);
        } else {
          setQuery("SELECT * FROM ");
        }
      } catch (err: unknown) {
        setErrorMsg(err instanceof Error ? err.message : "Failed to load problem details");
      } finally {
        setLoadingDetail(false);
      }
    };
    fetchDetail();
  }, [selectedSlug]);

  const handleSubmit = async () => {
    if (!selectedSlug) return;
    if (!isAuthenticated) {
      openAuthModal("login");
      return;
    }
    setSubmitting(true);
    setResult(null);
    try {
      const res = await sqlApi.submitQuery(selectedSlug, { query });
      setResult(res);
      if (res.is_correct) {
        // Update solved state in problem list
        setProblems((prev) =>
          prev.map((p) => (p.slug === selectedSlug ? { ...p, is_solved: true } : p))
        );
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Query execution failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "32px 20px" }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: "0 0 8px 0", fontSize: 28, fontWeight: 700, color: "#0f172a" }}>
          💾 Interactive SQL Learning Engine
        </h1>
        <p style={{ margin: 0, color: "#64748b", fontSize: 16 }}>
          Master SQL queries, window functions, and multi-table joins in an isolated, sandboxed environment.
        </p>
      </div>

      {errorMsg && (
        <div style={{ padding: 12, borderRadius: 8, backgroundColor: "#fef2f2", color: "#991b1b", marginBottom: 20 }}>
          {errorMsg}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 24 }}>
        {/* Left Column: Problem List */}
        <div>
          <h3 style={{ margin: "0 0 12px 0", fontSize: 16, color: "#1e293b" }}>SQL Problems</h3>
          {loadingProbs ? (
            <p style={{ color: "#64748b" }}>Loading problems...</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {problems.map((p) => {
                const isSelected = p.slug === selectedSlug;
                return (
                  <div
                    key={p.id}
                    onClick={() => setSelectedSlug(p.slug)}
                    style={{
                      padding: "12px 14px",
                      borderRadius: 8,
                      border: isSelected ? "2px solid #2563eb" : "1px solid #e2e8f0",
                      backgroundColor: isSelected ? "#eff6ff" : "#ffffff",
                      cursor: "pointer",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, color: "#0f172a", fontSize: 14 }}>
                        {p.title}
                      </div>
                      <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>
                        {p.category} • {p.difficulty}
                      </div>
                    </div>
                    {p.is_solved && <span style={{ color: "#16a34a", fontWeight: 700 }}>✓</span>}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Problem Workspace & Editor */}
        <div>
          {loadingDetail || !problemDetail ? (
            <div style={{ padding: 40, textAlign: "center", color: "#64748b" }}>Loading workspace...</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              {/* Problem Description Card */}
              <div
                style={{
                  padding: 20,
                  borderRadius: 12,
                  backgroundColor: "#ffffff",
                  border: "1px solid #e2e8f0",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <h2 style={{ margin: 0, fontSize: 20, color: "#0f172a" }}>
                    {problemDetail.title}
                  </h2>
                  <span
                    style={{
                      fontSize: 12,
                      fontWeight: 700,
                      padding: "2px 8px",
                      borderRadius: 4,
                      backgroundColor:
                        problemDetail.difficulty === "HARD"
                          ? "#fee2e2"
                          : problemDetail.difficulty === "MEDIUM"
                          ? "#fef3c7"
                          : "#ecfdf5",
                      color:
                        problemDetail.difficulty === "HARD"
                          ? "#991b1b"
                          : problemDetail.difficulty === "MEDIUM"
                          ? "#92400e"
                          : "#065f46",
                    }}
                  >
                    {problemDetail.difficulty}
                  </span>
                </div>

                <p style={{ margin: "0 0 16px 0", color: "#334155", fontSize: 15, lineHeight: 1.5 }}>
                  {problemDetail.description}
                </p>

                {/* Schema Explorer */}
                <div style={{ backgroundColor: "#f8fafc", padding: 14, borderRadius: 8, border: "1px solid #e2e8f0" }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: "#64748b", textTransform: "uppercase", marginBottom: 8 }}>
                    Table Schemas & Sample Rows
                  </div>
                  {problemDetail.parsed_schemas.map((schema) => (
                    <div key={schema.table_name} style={{ marginBottom: 10 }}>
                      <div style={{ fontWeight: 600, fontSize: 13, color: "#1e293b", marginBottom: 4 }}>
                        Table: <span style={{ fontFamily: "monospace", color: "#2563eb" }}>{schema.table_name}</span>
                      </div>
                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                        {schema.columns.map((col) => (
                          <span
                            key={col.name}
                            style={{
                              fontSize: 11,
                              padding: "2px 6px",
                              backgroundColor: "#ffffff",
                              border: "1px solid #cbd5e1",
                              borderRadius: 4,
                              fontFamily: "monospace",
                            }}
                          >
                            {col.name}: <strong>{col.type}</strong> {col.is_pk ? "(PK)" : ""}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Hints Toggle */}
                {problemDetail.hints && problemDetail.hints.length > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <button
                      onClick={() => setShowHints(!showHints)}
                      style={{
                        background: "none",
                        border: "none",
                        padding: 0,
                        fontSize: 13,
                        fontWeight: 600,
                        color: "#2563eb",
                        cursor: "pointer",
                      }}
                    >
                      {showHints ? "Hide Hints" : "💡 Show Hints"}
                    </button>
                    {showHints && (
                      <ul style={{ margin: "8px 0 0 0", paddingLeft: 20, fontSize: 13, color: "#475569" }}>
                        {problemDetail.hints.map((h, i) => (
                          <li key={i}>{h}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>

              {/* SQL Query Editor Card */}
              <div
                style={{
                  padding: 20,
                  borderRadius: 12,
                  backgroundColor: "#ffffff",
                  border: "1px solid #e2e8f0",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <label style={{ fontSize: 14, fontWeight: 600, color: "#0f172a" }}>
                    Your SQL Solution:
                  </label>
                  <span style={{ fontSize: 12, color: "#64748b" }}>
                    🔒 Read-Only Ephemeral Sandbox (AST Firewall Active)
                  </span>
                </div>

                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  rows={8}
                  style={{
                    width: "100%",
                    boxSizing: "border-box",
                    fontFamily: "monospace",
                    fontSize: 14,
                    padding: 12,
                    borderRadius: 8,
                    border: "1px solid #cbd5e1",
                    backgroundColor: "#0f172a",
                    color: "#f8fafc",
                    resize: "vertical",
                    marginBottom: 12,
                  }}
                />

                <div style={{ display: "flex", justifyContent: "flex-end" }}>
                  <button
                    onClick={handleSubmit}
                    disabled={submitting}
                    style={{
                      padding: "10px 24px",
                      borderRadius: 8,
                      backgroundColor: "#2563eb",
                      color: "#ffffff",
                      fontWeight: 600,
                      border: "none",
                      cursor: submitting ? "wait" : "pointer",
                    }}
                  >
                    {submitting ? "Executing SQL..." : "Run Query 🚀"}
                  </button>
                </div>
              </div>

              {/* Submission Result / Execution Grid */}
              {result && (
                <div
                  style={{
                    padding: 20,
                    borderRadius: 12,
                    backgroundColor: "#ffffff",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                      <span
                        style={{
                          fontSize: 14,
                          fontWeight: 700,
                          padding: "4px 12px",
                          borderRadius: 6,
                          backgroundColor: result.is_correct ? "#ecfdf5" : "#fee2e2",
                          color: result.is_correct ? "#065f46" : "#991b1b",
                        }}
                      >
                        {result.verdict}
                      </span>
                      <span style={{ fontSize: 13, color: "#64748b" }}>
                        Execution: {result.execution_time_ms} ms
                      </span>
                    </div>

                    {result.is_correct && result.xp_awarded > 0 && (
                      <span style={{ fontSize: 13, fontWeight: 700, color: "#059669" }}>
                        +{result.xp_awarded} XP Awarded! 🎉
                      </span>
                    )}
                  </div>

                  {result.error_message && (
                    <div
                      style={{
                        padding: 12,
                        borderRadius: 6,
                        backgroundColor: "#fef2f2",
                        color: "#991b1b",
                        fontFamily: "monospace",
                        fontSize: 13,
                        marginBottom: 16,
                      }}
                    >
                      {result.error_message}
                    </div>
                  )}

                  {/* Query Output Tables */}
                  <div style={{ display: "grid", gridTemplateColumns: result.expected_result ? "1fr 1fr" : "1fr", gap: 16 }}>
                    {result.user_result && (
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 700, color: "#475569", marginBottom: 6 }}>
                          YOUR OUTPUT ({result.user_result.row_count} rows)
                        </div>
                        <div style={{ overflowX: "auto", border: "1px solid #e2e8f0", borderRadius: 6 }}>
                          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, textAlign: "left" }}>
                            <thead>
                              <tr style={{ backgroundColor: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
                                {result.user_result.columns.map((c) => (
                                  <th key={c} style={{ padding: "6px 10px", color: "#475569" }}>{c}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {result.user_result.rows.map((row, rIdx) => (
                                <tr key={rIdx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                                  {row.map((val, cIdx) => (
                                    <td key={cIdx} style={{ padding: "6px 10px", fontFamily: "monospace" }}>
                                      {String(val ?? "NULL")}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {result.expected_result && (
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 700, color: "#475569", marginBottom: 6 }}>
                          EXPECTED OUTPUT ({result.expected_result.row_count} rows)
                        </div>
                        <div style={{ overflowX: "auto", border: "1px solid #e2e8f0", borderRadius: 6 }}>
                          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, textAlign: "left" }}>
                            <thead>
                              <tr style={{ backgroundColor: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
                                {result.expected_result.columns.map((c) => (
                                  <th key={c} style={{ padding: "6px 10px", color: "#475569" }}>{c}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {result.expected_result.rows.map((row, rIdx) => (
                                <tr key={rIdx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                                  {row.map((val, cIdx) => (
                                    <td key={cIdx} style={{ padding: "6px 10px", fontFamily: "monospace" }}>
                                      {String(val ?? "NULL")}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
