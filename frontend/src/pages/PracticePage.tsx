import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.tsx";
import { gamificationApi } from "../services/gamificationApi.ts";
import {
  PracticeMode,
  PracticeSession,
  ProblemRecommendation,
  RecommendationExplanation,
} from "../types/gamification.ts";

interface PracticePageProps {
  onNavigate: (path: string) => void;
}

const PRACTICE_MODES: {
  id: PracticeMode;
  title: string;
  desc: string;
  icon: string;
  isPro?: boolean;
}[] = [
  {
    id: "QUICK",
    title: "Quick Adaptive Drill",
    desc: "Intelligently calibrated problems tailored to your current skill rating.",
    icon: "⚡",
  },
  {
    id: "REVISION",
    title: "Spaced Retention",
    desc: "Revisit previously solved concepts before your memory decay interval expires.",
    icon: "🔄",
  },
  {
    id: "WEAK_AREA",
    title: "Weak Area Focus",
    desc: "Target topics where recent failure patterns or concept gaps were identified.",
    icon: "🧠",
    isPro: true,
  },
  {
    id: "MISTAKES",
    title: "Mistake Reinforcement",
    desc: "Directly re-engage with problems where bug logs and runtime errors occurred.",
    icon: "⚠️",
    isPro: true,
  },
];

export const PracticePage: React.FC<PracticePageProps> = ({ onNavigate }) => {
  const { isAuthenticated, isPremium, openAuthModal } = useAuth();

  const [selectedMode, setSelectedMode] = useState<PracticeMode>("QUICK");
  const [targetCount, setTargetCount] = useState<number>(3);
  const [activeSession, setActiveSession] = useState<PracticeSession | null>(null);
  const [currentProbIndex, setCurrentProbIndex] = useState<number>(0);
  const [timeSpent, setTimeSpent] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [sessionSummary, setSessionSummary] = useState<PracticeSession | null>(null);

  // Recommendations state
  const [recommendations, setRecommendations] = useState<ProblemRecommendation[]>([]);
  const [selectedExplanation, setSelectedExplanation] = useState<RecommendationExplanation | null>(null);
  const [history, setHistory] = useState<PracticeSession[]>([]);

  // Timer for active problem
  useEffect(() => {
    let timer: ReturnType<typeof setInterval>;
    if (activeSession && activeSession.status === "IN_PROGRESS") {
      timer = setInterval(() => {
        setTimeSpent((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [activeSession]);

  // Load recommendations and history
  useEffect(() => {
    if (isAuthenticated) {
      gamificationApi
        .getRecommendations(selectedMode)
        .then(setRecommendations)
        .catch(() => {});

      gamificationApi
        .getPracticeHistory(5)
        .then(setHistory)
        .catch(() => {});
    }
  }, [isAuthenticated, selectedMode]);

  const handleStartSession = async (modeToUse: PracticeMode = selectedMode) => {
    if (!isAuthenticated) {
      openAuthModal("login");
      return;
    }

    if ((modeToUse === "WEAK_AREA" || modeToUse === "MISTAKES") && !isPremium) {
      onNavigate("/premium");
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    try {
      const session = await gamificationApi.createPracticeSession(modeToUse, targetCount);
      setActiveSession(session);
      setCurrentProbIndex(0);
      setTimeSpent(0);
      setSessionSummary(null);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to start practice session.");
    } finally {
      setLoading(false);
    }
  };

  const handleRecordResult = async (solved: boolean) => {
    if (!activeSession) return;
    const currentProb = activeSession.problems[currentProbIndex];
    if (!currentProb) return;

    setLoading(true);
    try {
      await gamificationApi.recordProblemResult(
        activeSession.id,
        currentProb.problem_id,
        solved,
        timeSpent
      );

      // Check if there are more problems
      if (currentProbIndex + 1 < activeSession.problems.length) {
        setCurrentProbIndex((prev) => prev + 1);
        setTimeSpent(0);
        // Refresh session
        const updated = await gamificationApi.getPracticeSession(activeSession.id);
        setActiveSession(updated);
      } else {
        // Complete session
        const completed = await gamificationApi.completePracticeSession(activeSession.id);
        setActiveSession(null);
        setSessionSummary(completed);
        // Refresh history
        gamificationApi.getPracticeHistory(5).then(setHistory).catch(() => {});
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to record problem result.");
    } finally {
      setLoading(false);
    }
  };

  const handleExplainProblem = async (problemId: string) => {
    try {
      const expl = await gamificationApi.explainRecommendation(problemId);
      setSelectedExplanation(expl);
    } catch (err) {
      console.error("Could not fetch explanation", err);
    }
  };

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "var(--space-8) var(--space-4)", width: "100%" }}>
      {/* Header section */}
      <div style={{ marginBottom: "var(--space-8)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "var(--space-4)" }}>
          <div>
            <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: 0 }}>Practice Engine</h1>
            <p style={{ color: "var(--text-secondary)", marginTop: "var(--space-2)" }}>
              Targeted, adaptive problem sets with real-time feedback and server-authoritative XP.
            </p>
          </div>
          <div style={{ display: "flex", gap: "var(--space-3)" }}>
            <button
              onClick={() => onNavigate("/daily")}
              style={{
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-primary)",
                padding: "8px 16px",
                borderRadius: "var(--radius-md)",
                cursor: "pointer",
                fontWeight: 600,
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <span>📅</span> Daily Challenge
            </button>
            <button
              onClick={() => onNavigate("/leaderboard")}
              style={{
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-primary)",
                padding: "8px 16px",
                borderRadius: "var(--radius-md)",
                cursor: "pointer",
                fontWeight: 600,
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <span>🏆</span> Leaderboard
            </button>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div
          style={{
            backgroundColor: "var(--status-danger-bg)",
            color: "var(--status-danger)",
            padding: "var(--space-4)",
            borderRadius: "var(--radius-md)",
            marginBottom: "var(--space-6)",
            border: "1px solid var(--status-danger)",
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* Active Session Runner */}
      {activeSession && activeSession.status === "IN_PROGRESS" && (
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--brand-primary)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
            marginBottom: "var(--space-8)",
            boxShadow: "0 0 20px rgba(59, 130, 246, 0.15)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "var(--space-4)", marginBottom: "var(--space-4)" }}>
            <div>
              <span style={{ fontSize: "0.8125rem", color: "var(--brand-primary)", fontWeight: 700, textTransform: "uppercase" }}>
                Session In Progress • {activeSession.mode}
              </span>
              <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "4px 0 0 0" }}>
                Problem {currentProbIndex + 1} of {activeSession.problems.length}
              </h2>
            </div>
            <div style={{ display: "flex", gap: "var(--space-4)", alignItems: "center" }}>
              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Elapsed Time</span>
                <div style={{ fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: "1.125rem" }}>
                  {Math.floor(timeSpent / 60)}:{(timeSpent % 60).toString().padStart(2, "0")}
                </div>
              </div>
            </div>
          </div>

          {activeSession.problems[currentProbIndex] && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
                <div>
                  <h3 style={{ fontSize: "1.125rem", fontWeight: 600, margin: 0 }}>
                    {activeSession.problems[currentProbIndex].problem_title}
                  </h3>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      padding: "2px 8px",
                      borderRadius: "var(--radius-sm)",
                      backgroundColor: "var(--bg-tertiary)",
                      marginTop: "6px",
                      display: "inline-block",
                    }}
                  >
                    {activeSession.problems[currentProbIndex].difficulty}
                  </span>
                </div>
                <button
                  onClick={() => onNavigate(`/problems/${activeSession.problems[currentProbIndex].problem_id}`)}
                  style={{
                    backgroundColor: "var(--brand-primary)",
                    color: "#ffffff",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: "var(--radius-md)",
                    cursor: "pointer",
                    fontWeight: 600,
                  }}
                >
                  Open in Code Workspace ↗
                </button>
              </div>

              <div
                style={{
                  display: "flex",
                  gap: "var(--space-3)",
                  justifyContent: "flex-end",
                  borderTop: "1px solid var(--border-subtle)",
                  paddingTop: "var(--space-4)",
                  marginTop: "var(--space-6)",
                }}
              >
                <button
                  disabled={loading}
                  onClick={() => handleRecordResult(false)}
                  style={{
                    backgroundColor: "var(--bg-tertiary)",
                    border: "1px solid var(--border-muted)",
                    color: "var(--text-secondary)",
                    padding: "10px 18px",
                    borderRadius: "var(--radius-md)",
                    cursor: "pointer",
                    fontWeight: 600,
                  }}
                >
                  Skip / Need Help
                </button>
                <button
                  disabled={loading}
                  onClick={() => handleRecordResult(true)}
                  style={{
                    backgroundColor: "var(--status-success)",
                    border: "none",
                    color: "#ffffff",
                    padding: "10px 24px",
                    borderRadius: "var(--radius-md)",
                    cursor: "pointer",
                    fontWeight: 700,
                  }}
                >
                  ✓ Mark Solved & Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Session Completed Summary Banner */}
      {sessionSummary && (
        <div
          style={{
            backgroundColor: "rgba(16, 185, 129, 0.1)",
            border: "1px solid var(--status-success)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
            marginBottom: "var(--space-8)",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "2.5rem", marginBottom: "var(--space-2)" }}>🎉</div>
          <h2 style={{ fontSize: "1.5rem", fontWeight: 800, margin: 0, color: "var(--status-success)" }}>
            Session Completed!
          </h2>
          <p style={{ color: "var(--text-secondary)", marginTop: "4px" }}>
            Great consistency! Your practice metrics have been committed to the server.
          </p>

          <div
            style={{
              display: "flex",
              justifyContent: "center",
              gap: "var(--space-8)",
              margin: "var(--space-6) 0",
              flexWrap: "wrap",
            }}
          >
            <div>
              <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--brand-primary)" }}>
                +{sessionSummary.xp_earned} XP
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>XP Earned</div>
            </div>
            <div>
              <div style={{ fontSize: "1.5rem", fontWeight: 800 }}>
                {Math.round(sessionSummary.accuracy * 100)}%
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Accuracy</div>
            </div>
            <div>
              <div style={{ fontSize: "1.5rem", fontWeight: 800 }}>
                {sessionSummary.solved_count} / {sessionSummary.target_count}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Problems Solved</div>
            </div>
            <div>
              <div style={{ fontSize: "1.5rem", fontWeight: 800 }}>
                {Math.round(sessionSummary.duration_seconds / 60)}m
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Time Spent</div>
            </div>
          </div>

          <button
            onClick={() => setSessionSummary(null)}
            style={{
              backgroundColor: "var(--status-success)",
              color: "#ffffff",
              border: "none",
              padding: "8px 20px",
              borderRadius: "var(--radius-md)",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Start Another Drill
          </button>
        </div>
      )}

      {/* Mode Selector */}
      {!activeSession && !sessionSummary && (
        <div style={{ marginBottom: "var(--space-8)" }}>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "var(--space-4)" }}>
            Choose Practice Mode
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: "var(--space-4)",
            }}
          >
            {PRACTICE_MODES.map((mode) => {
              const isSelected = selectedMode === mode.id;
              const isLocked = mode.isPro && !isPremium;

              return (
                <div
                  key={mode.id}
                  onClick={() => {
                    if (isLocked) {
                      onNavigate("/premium");
                    } else {
                      setSelectedMode(mode.id);
                    }
                  }}
                  style={{
                    backgroundColor: isSelected ? "var(--bg-tertiary)" : "var(--bg-secondary)",
                    border: isSelected
                      ? "2px solid var(--brand-primary)"
                      : "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-lg)",
                    padding: "var(--space-5)",
                    cursor: "pointer",
                    position: "relative",
                    transition: "all 0.15s ease",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "1.5rem" }}>{mode.icon}</span>
                    {mode.isPro && (
                      <span
                        style={{
                          fontSize: "0.6875rem",
                          fontWeight: 700,
                          padding: "2px 6px",
                          borderRadius: "var(--radius-sm)",
                          backgroundColor: "rgba(234, 179, 8, 0.2)",
                          color: "var(--status-warning)",
                          border: "1px solid var(--status-warning)",
                        }}
                      >
                        PRO
                      </span>
                    )}
                  </div>
                  <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: "var(--space-2) 0 4px 0" }}>
                    {mode.title}
                  </h3>
                  <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", margin: 0, lineHeight: 1.4 }}>
                    {mode.desc}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Drill Options & Launch */}
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-6)",
              marginTop: "var(--space-6)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "var(--space-4)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
              <span style={{ fontSize: "0.875rem", fontWeight: 600 }}>Problems in Drill:</span>
              {[3, 5, 10].map((num) => (
                <button
                  key={num}
                  onClick={() => setTargetCount(num)}
                  style={{
                    backgroundColor: targetCount === num ? "var(--brand-primary)" : "var(--bg-tertiary)",
                    color: targetCount === num ? "#ffffff" : "var(--text-primary)",
                    border: "1px solid var(--border-muted)",
                    padding: "6px 14px",
                    borderRadius: "var(--radius-md)",
                    cursor: "pointer",
                    fontWeight: 600,
                    fontSize: "0.875rem",
                  }}
                >
                  {num} Problems
                </button>
              ))}
            </div>

            <button
              disabled={loading}
              onClick={() => handleStartSession()}
              style={{
                backgroundColor: "var(--brand-primary)",
                color: "#ffffff",
                border: "none",
                padding: "10px 28px",
                borderRadius: "var(--radius-md)",
                cursor: "pointer",
                fontWeight: 700,
                fontSize: "1rem",
                boxShadow: "0 4px 14px rgba(59, 130, 246, 0.3)",
              }}
            >
              {loading ? "Initializing..." : "Start Practice Session →"}
            </button>
          </div>
        </div>
      )}

      {/* Intelligent Recommendations */}
      {recommendations.length > 0 && (
        <div style={{ marginBottom: "var(--space-8)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>
              AI Problem Recommendations
            </h2>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Calibrated by Spaced Repetition & Cognitive Weaknesses
            </span>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
              gap: "var(--space-4)",
            }}
          >
            {recommendations.map((rec) => (
              <div
                key={rec.problem_id}
                style={{
                  backgroundColor: "var(--bg-secondary)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-lg)",
                  padding: "var(--space-5)",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-2)" }}>
                    <span
                      style={{
                        fontSize: "0.6875rem",
                        fontWeight: 700,
                        padding: "2px 8px",
                        borderRadius: "var(--radius-sm)",
                        backgroundColor: "var(--bg-tertiary)",
                        color: "var(--brand-primary)",
                      }}
                    >
                      {rec.category}
                    </span>
                    <span
                      style={{
                        fontSize: "0.6875rem",
                        fontWeight: 600,
                        color: "var(--text-muted)",
                      }}
                    >
                      {rec.difficulty}
                    </span>
                  </div>
                  <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: "0 0 6px 0" }}>{rec.title}</h3>
                  <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", margin: 0, lineHeight: 1.4 }}>
                    {rec.reasons[0] || "Recommended for balanced growth."}
                  </p>
                </div>

                <div style={{ display: "flex", gap: "var(--space-2)", marginTop: "var(--space-4)" }}>
                  <button
                    onClick={() => handleExplainProblem(rec.problem_id)}
                    style={{
                      flex: 1,
                      backgroundColor: "var(--bg-tertiary)",
                      border: "1px solid var(--border-muted)",
                      color: "var(--text-secondary)",
                      padding: "6px 12px",
                      borderRadius: "var(--radius-md)",
                      cursor: "pointer",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                    }}
                  >
                    Why this?
                  </button>
                  <button
                    onClick={() => onNavigate(`/problems/${rec.problem_id}`)}
                    style={{
                      flex: 1,
                      backgroundColor: "var(--brand-primary)",
                      border: "none",
                      color: "#ffffff",
                      padding: "6px 12px",
                      borderRadius: "var(--radius-md)",
                      cursor: "pointer",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                    }}
                  >
                    Solve Now ↗
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explanation Modal */}
      {selectedExplanation && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "var(--space-4)",
          }}
        >
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              maxWidth: "500px",
              width: "100%",
              padding: "var(--space-6)",
            }}
          >
            <h3 style={{ fontSize: "1.125rem", fontWeight: 700, margin: 0 }}>
              Why We Recommend: {selectedExplanation.title}
            </h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", margin: "var(--space-3) 0" }}>
              {selectedExplanation.explanation}
            </p>

            <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "var(--space-3)" }}>
              <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
                Pedagogical Factors
              </div>
              <ul style={{ margin: "var(--space-2) 0 0 0", paddingLeft: "var(--space-5)", fontSize: "0.8125rem" }}>
                {selectedExplanation.pedagogical_factors.map((factor, i) => (
                  <li key={i} style={{ marginBottom: "4px" }}>
                    {factor}
                  </li>
                ))}
              </ul>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "var(--space-6)" }}>
              <button
                onClick={() => setSelectedExplanation(null)}
                style={{
                  backgroundColor: "var(--bg-tertiary)",
                  border: "1px solid var(--border-muted)",
                  color: "var(--text-primary)",
                  padding: "6px 16px",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  fontWeight: 600,
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Recent History Table */}
      {history.length > 0 && (
        <div>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "var(--space-4)" }}>
            Recent Practice Drills
          </h2>
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              overflow: "hidden",
            }}
          >
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)", backgroundColor: "var(--bg-tertiary)" }}>
                  <th style={{ padding: "10px 16px" }}>Date</th>
                  <th style={{ padding: "10px 16px" }}>Mode</th>
                  <th style={{ padding: "10px 16px" }}>Solved</th>
                  <th style={{ padding: "10px 16px" }}>Accuracy</th>
                  <th style={{ padding: "10px 16px" }}>XP Earned</th>
                </tr>
              </thead>
              <tbody>
                {history.map((sess) => (
                  <tr key={sess.id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "12px 16px", color: "var(--text-muted)" }}>
                      {new Date(sess.started_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: "12px 16px", fontWeight: 600 }}>{sess.mode}</td>
                    <td style={{ padding: "12px 16px" }}>
                      {sess.solved_count} / {sess.target_count}
                    </td>
                    <td style={{ padding: "12px 16px" }}>{Math.round(sess.accuracy * 100)}%</td>
                    <td style={{ padding: "12px 16px", color: "var(--brand-primary)", fontWeight: 700 }}>
                      +{sess.xp_earned} XP
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
