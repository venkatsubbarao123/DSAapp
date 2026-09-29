import React, { useEffect, useState } from "react";
import { interviewApi } from "../services/interviewApi.ts";
import { InterviewEvaluationReport } from "../types/interview.ts";

interface InterviewReportPageProps {
  sessionId: string;
  onNavigate: (path: string) => void;
}

export const InterviewReportPage: React.FC<InterviewReportPageProps> = ({
  sessionId,
  onNavigate,
}) => {
  const [report, setReport] = useState<InterviewEvaluationReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const data = await interviewApi.getReport(sessionId);
        setReport(data);
      } catch (err: unknown) {
        setErrorMsg(err instanceof Error ? err.message : "Failed to load report");
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [sessionId]);

  if (loading) {
    return (
      <div style={{ maxWidth: 800, margin: "60px auto", textAlign: "center" }}>
        Analyzing interview performance and calculating rubric scores...
      </div>
    );
  }

  if (errorMsg || !report) {
    return (
      <div style={{ maxWidth: 700, margin: "60px auto", padding: 24, textAlign: "center" }}>
        <h2>Report Not Available</h2>
        <p style={{ color: "#dc2626" }}>{errorMsg || "Unable to display evaluation report."}</p>
        <button
          onClick={() => onNavigate("/interview")}
          style={{
            padding: "8px 16px",
            backgroundColor: "#2563eb",
            color: "#fff",
            borderRadius: 6,
            border: "none",
            cursor: "pointer",
          }}
        >
          Return to Interviews
        </button>
      </div>
    );
  }

  const getVerdictBadgeColor = (verdict: string) => {
    switch (verdict) {
      case "STRONG_HIRE":
        return { bg: "#dcfce7", text: "#15803d" };
      case "HIRE":
        return { bg: "#ecfdf5", text: "#059669" };
      case "LEAN_HIRE":
        return { bg: "#fef3c7", text: "#b45309" };
      default:
        return { bg: "#fee2e2", text: "#b91c1c" };
    }
  };

  const badgeColors = getVerdictBadgeColor(report.verdict);

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "32px 20px" }}>
      {/* Top Banner */}
      <div
        style={{
          padding: 32,
          borderRadius: 16,
          backgroundColor: "#ffffff",
          border: "1px solid #e2e8f0",
          marginBottom: 32,
          textAlign: "center",
          boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
        }}
      >
        <div style={{ fontSize: 13, fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: 1 }}>
          Technical Interview Diagnostic
        </div>
        <h1 style={{ margin: "8px 0 16px 0", fontSize: 32, color: "#0f172a" }}>
          Evaluation Scorecard
        </h1>

        <div style={{ display: "inline-block", padding: "8px 24px", borderRadius: 9999, backgroundColor: badgeColors.bg, color: badgeColors.text, fontWeight: 700, fontSize: 18, marginBottom: 16 }}>
          {report.verdict.replace("_", " ")}
        </div>

        <div style={{ fontSize: 48, fontWeight: 800, color: "#2563eb", margin: "8px 0" }}>
          {report.overall_score} <span style={{ fontSize: 24, color: "#64748b" }}>/ 100</span>
        </div>

        <p style={{ maxWidth: 650, margin: "12px auto 0 auto", color: "#475569", fontSize: 15, lineHeight: 1.6 }}>
          {report.feedback_summary}
        </p>
      </div>

      {/* Rubric Breakdown Grid */}
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: "#1e293b", marginBottom: 16 }}>
          Competency Rubric Assessment
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
          {Object.entries(report.rubric_breakdown).map(([category, score]) => (
            <div
              key={category}
              style={{
                padding: 16,
                borderRadius: 10,
                backgroundColor: "#ffffff",
                border: "1px solid #e2e8f0",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: "#475569", textTransform: "capitalize" }}>
                  {category.replace("_", " ")}
                </span>
                <span style={{ fontSize: 14, fontWeight: 700, color: "#0f172a" }}>
                  {score}%
                </span>
              </div>
              <div style={{ width: "100%", height: 8, backgroundColor: "#f1f5f9", borderRadius: 9999, overflow: "hidden" }}>
                <div
                  style={{
                    height: "100%",
                    width: `${Math.min(100, Math.max(0, score))}%`,
                    backgroundColor: score >= 75 ? "#10b981" : score >= 50 ? "#3b82f6" : "#f59e0b",
                    borderRadius: 9999,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Strengths & Improvement Areas */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 32 }}>
        <div
          style={{
            padding: 20,
            borderRadius: 12,
            backgroundColor: "#f0fdf4",
            border: "1px solid #bbf7d0",
          }}
        >
          <h3 style={{ margin: "0 0 12px 0", fontSize: 16, color: "#166534" }}>
            🌟 Demonstrated Strengths
          </h3>
          <ul style={{ margin: 0, paddingLeft: 20, color: "#166534", fontSize: 14, lineHeight: 1.6 }}>
            {report.strengths.map((s, idx) => (
              <li key={idx} style={{ marginBottom: 6 }}>{s}</li>
            ))}
          </ul>
        </div>

        <div
          style={{
            padding: 20,
            borderRadius: 12,
            backgroundColor: "#fefce8",
            border: "1px solid #fef08a",
          }}
        >
          <h3 style={{ margin: "0 0 12px 0", fontSize: 16, color: "#854d0e" }}>
            🎯 Target Improvement Focus
          </h3>
          <ul style={{ margin: 0, paddingLeft: 20, color: "#854d0e", fontSize: 14, lineHeight: 1.6 }}>
            {report.improvement_areas.map((area, idx) => (
              <li key={idx} style={{ marginBottom: 6 }}>{area}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Recommended Practice Problems */}
      {report.recommended_problems && report.recommended_problems.length > 0 && (
        <div style={{ marginBottom: 40 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "#1e293b", marginBottom: 16 }}>
            Recommended Remediation Problems
          </h2>
          <div style={{ display: "grid", gap: 12 }}>
            {report.recommended_problems.map((p) => (
              <div
                key={p.problem_id}
                onClick={() => onNavigate(`/problems/${p.problem_id}`)}
                style={{
                  padding: "14px 18px",
                  borderRadius: 8,
                  backgroundColor: "#ffffff",
                  border: "1px solid #e2e8f0",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  cursor: "pointer",
                }}
              >
                <div>
                  <span style={{ fontWeight: 600, color: "#0f172a" }}>{p.title}</span>
                  <span
                    style={{
                      marginLeft: 10,
                      fontSize: 12,
                      padding: "2px 8px",
                      borderRadius: 4,
                      backgroundColor: p.difficulty === "HARD" ? "#fee2e2" : p.difficulty === "MEDIUM" ? "#fef3c7" : "#ecfdf5",
                      color: p.difficulty === "HARD" ? "#991b1b" : p.difficulty === "MEDIUM" ? "#92400e" : "#065f46",
                    }}
                  >
                    {p.difficulty}
                  </span>
                </div>
                <span style={{ fontSize: 14, color: "#2563eb", fontWeight: 600 }}>Solve →</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bottom Actions */}
      <div style={{ display: "flex", justifyContent: "center", gap: 16 }}>
        <button
          onClick={() => onNavigate("/interview")}
          style={{
            padding: "10px 24px",
            borderRadius: 8,
            backgroundColor: "#2563eb",
            color: "#ffffff",
            fontWeight: 600,
            border: "none",
            cursor: "pointer",
          }}
        >
          New Interview Drill
        </button>
        <button
          onClick={() => onNavigate("/practice")}
          style={{
            padding: "10px 24px",
            borderRadius: 8,
            backgroundColor: "#f1f5f9",
            color: "#334155",
            fontWeight: 600,
            border: "1px solid #cbd5e1",
            cursor: "pointer",
          }}
        >
          Adaptive Practice
        </button>
      </div>
    </div>
  );
};
