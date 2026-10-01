import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.tsx";
import { interviewApi } from "../services/interviewApi.ts";
import {
  InterviewMode,
  InterviewSessionSummary,
} from "../types/interview.ts";

interface InterviewPageProps {
  onNavigate: (path: string) => void;
}

const INTERVIEW_MODES: {
  mode: InterviewMode;
  title: string;
  badge: string;
  desc: string;
  icon: string;
}[] = [
  {
    mode: "MOCK_TECHNICAL",
    title: "Full Technical Mock",
    badge: "Core",
    desc: "Rigorous 45-minute live interview covering problem solving, algorithmic efficiency, and live code walk-through.",
    icon: "💻",
  },
  {
    mode: "COMPANY_FAANG",
    title: "FAANG / Big Tech Drill",
    badge: "High Bar",
    desc: "Calibrated to Google, Meta, and Amazon rubrics with strict time complexity and edge case interrogation.",
    icon: "🏢",
  },
  {
    mode: "COMPANY_STARTUP",
    title: "Startup & Pragmatic Eng",
    badge: "Applied",
    desc: "Focus on clean architecture, practical decision making, concurrency, and rapid feature delivery.",
    icon: "🚀",
  },
  {
    mode: "SPEED_DSA",
    title: "Rapid Fire DSA Blitz",
    badge: "30 Min",
    desc: "Fast-paced algorithmic challenge testing pattern recognition, intuition, and immediate code fluency.",
    icon: "⚡",
  },
  {
    mode: "SYSTEM_DESIGN",
    title: "System Architecture & Design",
    badge: "Senior",
    desc: "High-level design, database sharding, caching, CAP theorem tradeoffs, and API schema design.",
    icon: "📐",
  },
  {
    mode: "PAIR_PROGRAMMING",
    title: "Collaborative Pair Coding",
    badge: "Interactive",
    desc: "Live problem discussion with an interactive AI pair partner asking questions and probing assumptions.",
    icon: "👥",
  },
  {
    mode: "BEHAVIORAL",
    title: "Behavioral & STAR Method",
    badge: "Leadership",
    desc: "Leadership principles, conflict resolution, ambiguity handling, and project post-mortems.",
    icon: "🗣️",
  },
];

export const InterviewPage: React.FC<InterviewPageProps> = ({ onNavigate }) => {
  const { isAuthenticated, openAuthModal } = useAuth();

  const [selectedMode, setSelectedMode] = useState<InterviewMode>("MOCK_TECHNICAL");
  const [targetCompany, setTargetCompany] = useState<string>("Google");
  const [targetRole, setTargetRole] = useState<string>("Senior Software Engineer");
  const [difficulty, setDifficulty] = useState<string>("MEDIUM");
  const [durationMinutes, setDurationMinutes] = useState<number>(45);

  const [pastSessions, setPastSessions] = useState<InterviewSessionSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [starting, setStarting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadPastSessions = async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const data = await interviewApi.getSessions();
      setPastSessions(data);
    } catch (err: unknown) {
      console.error("Failed to load interview sessions:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPastSessions();
  }, [isAuthenticated]);

  const handleStartSession = async () => {
    if (!isAuthenticated) {
      openAuthModal("login");
      return;
    }
    setStarting(true);
    setErrorMsg(null);
    try {
      const session = await interviewApi.startInterview({
        mode: selectedMode,
        target_company: targetCompany,
        target_role: targetRole,
        difficulty,
        duration_minutes: durationMinutes,
      });
      onNavigate(`/interview/${session.id}`);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to initiate session");
      setStarting(false);
    }
  };

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "32px 20px" }}>
      {/* Top Navigation */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, flexWrap: "wrap", gap: 10 }}>
        <button
          onClick={() => onNavigate("/")}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            padding: "8px 14px",
            borderRadius: 8,
            backgroundColor: "#f1f5f9",
            border: "1px solid #e2e8f0",
            color: "#0f172a",
            fontSize: 13,
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          🏠 Return to Home
        </button>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button
            onClick={() => onNavigate("/practice")}
            style={{
              padding: "6px 12px",
              borderRadius: 6,
              backgroundColor: "transparent",
              border: "1px solid #e2e8f0",
              color: "#64748b",
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            Practice Hub
          </button>
          <button
            onClick={() => onNavigate("/problems")}
            style={{
              padding: "6px 12px",
              borderRadius: 6,
              backgroundColor: "transparent",
              border: "1px solid #e2e8f0",
              color: "#64748b",
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            Problem Library
          </button>
        </div>
      </div>

      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ margin: "0 0 8px 0", fontSize: 28, fontWeight: 700, color: "var(--color-text-primary, #0f172a)" }}>
          🎯 AI Technical Interview Simulator
        </h1>
        <p style={{ margin: 0, color: "var(--color-text-secondary, #64748b)", fontSize: 16 }}>
          Realistic interview drills with authoritative timers, multi-stage rubrics, and deep post-interview diagnostics.
        </p>
      </div>

      {errorMsg && (
        <div
          style={{
            padding: 14,
            borderRadius: 8,
            backgroundColor: "#fef2f2",
            color: "#991b1b",
            border: "1px solid #fecaca",
            marginBottom: 24,
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* Mode Selection Grid */}
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16, color: "#1e293b" }}>
          Select Interview Track
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: 16,
          }}
        >
          {INTERVIEW_MODES.map((m) => {
            const isSelected = selectedMode === m.mode;
            return (
              <div
                key={m.mode}
                onClick={() => setSelectedMode(m.mode)}
                style={{
                  padding: 20,
                  borderRadius: 12,
                  border: isSelected ? "2px solid var(--color-primary, #2563eb)" : "1px solid var(--color-border, #e2e8f0)",
                  backgroundColor: isSelected ? "#eff6ff" : "var(--color-card-bg, #ffffff)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                  position: "relative",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                  <div style={{ fontSize: 28 }}>{m.icon}</div>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      padding: "2px 8px",
                      borderRadius: 9999,
                      backgroundColor: isSelected ? "#2563eb" : "#f1f5f9",
                      color: isSelected ? "#ffffff" : "#475569",
                    }}
                  >
                    {m.badge}
                  </span>
                </div>
                <h3 style={{ margin: "0 0 6px 0", fontSize: 16, fontWeight: 600, color: "#0f172a" }}>
                  {m.title}
                </h3>
                <p style={{ margin: 0, fontSize: 13, color: "#64748b", lineHeight: 1.4 }}>
                  {m.desc}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Session Configuration Card */}
      <div
        style={{
          padding: 24,
          borderRadius: 12,
          backgroundColor: "var(--color-card-bg, #ffffff)",
          border: "1px solid var(--color-border, #e2e8f0)",
          marginBottom: 40,
        }}
      >
        <h3 style={{ margin: "0 0 16px 0", fontSize: 16, fontWeight: 600, color: "#1e293b" }}>
          Session Customization
        </h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16, marginBottom: 20 }}>
          <div>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6, color: "#475569" }}>
              Target Company
            </label>
            <input
              type="text"
              value={targetCompany}
              onChange={(e) => setTargetCompany(e.target.value)}
              placeholder="e.g. Google, Meta, Stripe"
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 6,
                border: "1px solid #cbd5e1",
                fontSize: 14,
                boxSizing: "border-box",
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6, color: "#475569" }}>
              Target Role
            </label>
            <input
              type="text"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              placeholder="e.g. Staff Engineer, Backend"
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 6,
                border: "1px solid #cbd5e1",
                fontSize: 14,
                boxSizing: "border-box",
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6, color: "#475569" }}>
              Difficulty Level
            </label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 6,
                border: "1px solid #cbd5e1",
                fontSize: 14,
                backgroundColor: "#fff",
                boxSizing: "border-box",
              }}
            >
              <option value="EASY">Entry / College Grad</option>
              <option value="MEDIUM">Mid-Level Engineer</option>
              <option value="HARD">Senior / Staff / Tech Lead</option>
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6, color: "#475569" }}>
              Duration
            </label>
            <select
              value={durationMinutes}
              onChange={(e) => setDurationMinutes(Number(e.target.value))}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 6,
                border: "1px solid #cbd5e1",
                fontSize: 14,
                backgroundColor: "#fff",
                boxSizing: "border-box",
              }}
            >
              <option value={30}>30 Minutes</option>
              <option value={45}>45 Minutes (Standard)</option>
              <option value={60}>60 Minutes (In-Depth)</option>
            </select>
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button
            onClick={handleStartSession}
            disabled={starting}
            style={{
              padding: "12px 28px",
              borderRadius: 8,
              backgroundColor: "var(--color-primary, #2563eb)",
              color: "#ffffff",
              fontSize: 15,
              fontWeight: 600,
              border: "none",
              cursor: starting ? "wait" : "pointer",
            }}
          >
            {starting ? "Configuring Interview Room..." : "Begin Interview 🚀"}
          </button>
        </div>
      </div>

      {/* Past Sessions History */}
      <div>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16, color: "#1e293b" }}>
          Your Completed Interview Evaluations
        </h2>
        {!isAuthenticated ? (
          <p style={{ color: "#64748b" }}>Sign in to view your past interview assessments and scorecard reports.</p>
        ) : loading ? (
          <p style={{ color: "#64748b" }}>Loading interview history...</p>
        ) : pastSessions.length === 0 ? (
          <div
            style={{
              padding: "32px 20px",
              textAlign: "center",
              borderRadius: 8,
              backgroundColor: "#f8fafc",
              border: "1px dashed #cbd5e1",
              color: "#64748b",
            }}
          >
            No mock interviews completed yet. Start your first session above!
          </div>
        ) : (
          <div style={{ display: "grid", gap: 12 }}>
            {pastSessions.map((s) => (
              <div
                key={s.id}
                onClick={() => onNavigate(s.status !== "IN_PROGRESS" ? `/interview/${s.id}/report` : `/interview/${s.id}`)}
                style={{
                  padding: "16px 20px",
                  borderRadius: 8,
                  border: "1px solid #e2e8f0",
                  backgroundColor: "#fff",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  cursor: "pointer",
                }}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, color: "#0f172a" }}>{s.mode.replace("_", " ")}</span>
                    {s.target_company && (
                      <span style={{ fontSize: 12, color: "#64748b" }}>• {s.target_company}</span>
                    )}
                    <span
                      style={{
                        fontSize: 11,
                        padding: "1px 6px",
                        borderRadius: 4,
                        backgroundColor: s.status === "COMPLETED" ? "#ecfdf5" : s.status === "EXPIRED" ? "#fffbeb" : "#f1f5f9",
                        color: s.status === "COMPLETED" ? "#065f46" : s.status === "EXPIRED" ? "#b45309" : "#475569",
                      }}
                    >
                      {s.status}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: "#64748b" }}>
                    {new Date(s.created_at).toLocaleDateString()} • {s.answered_questions} of {s.total_questions} questions answered
                  </div>
                </div>

                <div style={{ textAlign: "right" }}>
                  {s.overall_score !== null && s.overall_score !== undefined && (
                    <div style={{ fontSize: 16, fontWeight: 700, color: "#2563eb" }}>
                      Score: {s.overall_score} / 100
                    </div>
                  )}
                  {s.verdict && (
                    <div style={{ fontSize: 12, fontWeight: 600, color: "#059669" }}>
                      {s.verdict}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
