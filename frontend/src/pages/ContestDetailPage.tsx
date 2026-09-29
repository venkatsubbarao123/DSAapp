import React, { useEffect, useState, useRef } from "react";
import { useAuth } from "../context/AuthContext.tsx";
import { contestApi } from "../services/contestApi.ts";
import {
  ContestDetail,
  ContestLeaderboard,
  ContestProblem,
  ContestSubmitResult,
} from "../types/contest.ts";

interface ContestDetailPageProps {
  slug: string;
  onNavigate: (path: string) => void;
}

export const ContestDetailPage: React.FC<ContestDetailPageProps> = ({ slug, onNavigate }) => {
  const { isAuthenticated, openAuthModal } = useAuth();

  const [contest, setContest] = useState<ContestDetail | null>(null);
  const [leaderboard, setLeaderboard] = useState<ContestLeaderboard | null>(null);
  const [activeTab, setActiveTab] = useState<"PROBLEMS" | "STANDINGS">("PROBLEMS");
  const [remainingSec, setRemainingSec] = useState<number>(0);
  const [selectedProblem, setSelectedProblem] = useState<ContestProblem | null>(null);

  // Submission drawer state
  const [sourceCode, setSourceCode] = useState<string>("# Write your solution here\n");
  const [language, setLanguage] = useState<string>("python");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitResult, setSubmitResult] = useState<ContestSubmitResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchDetail = async () => {
    try {
      const data = await contestApi.getContestDetail(slug);
      setContest(data);
      setRemainingSec(data.remaining_seconds);
      if (data.problems && data.problems.length > 0 && !selectedProblem) {
        setSelectedProblem(data.problems[0]);
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to load contest");
    } finally {
      setLoading(false);
    }
  };

  const fetchStandings = async () => {
    try {
      const lb = await contestApi.getLeaderboard(slug);
      setLeaderboard(lb);
    } catch (err) {
      console.error("Leaderboard load error:", err);
    }
  };

  useEffect(() => {
    fetchDetail();
    fetchStandings();
  }, [slug]);

  // Local ticker for countdown
  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setRemainingSec((prev) => {
        if (prev <= 1) {
          fetchDetail();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [contest?.status]);

  const handleRegister = async () => {
    if (!isAuthenticated) {
      openAuthModal("login");
      return;
    }
    try {
      const res = await contestApi.registerForContest(slug);
      setActionNotice(res.message);
      fetchDetail();
    } catch (err: unknown) {
      setActionNotice(err instanceof Error ? err.message : "Registration failed");
    }
  };

  const handleSubmit = async () => {
    if (!selectedProblem) return;
    if (!isAuthenticated) {
      openAuthModal("login");
      return;
    }
    setSubmitting(true);
    setSubmitResult(null);
    try {
      const res = await contestApi.submitSolution(slug, {
        problem_id: selectedProblem.problem_id,
        language,
        source_code: sourceCode,
      });
      setSubmitResult(res);
      fetchDetail();
      fetchStandings();
    } catch (err: unknown) {
      setActionNotice(err instanceof Error ? err.message : "Submission rejected");
    } finally {
      setSubmitting(false);
    }
  };

  const formatCountdown = (seconds: number) => {
    if (seconds <= 0) return "00:00:00";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  if (loading) {
    return (
      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "60px 20px", textAlign: "center" }}>
        Loading contest environment...
      </div>
    );
  }

  if (errorMsg || !contest) {
    return (
      <div style={{ maxWidth: 800, margin: "40px auto", padding: 24, textAlign: "center" }}>
        <h2>Contest Not Accessible</h2>
        <p style={{ color: "#dc2626" }}>{errorMsg || "Contest not found."}</p>
        <button
          onClick={() => onNavigate("/contests")}
          style={{
            padding: "8px 16px",
            backgroundColor: "var(--color-primary, #2563eb)",
            color: "#fff",
            borderRadius: 6,
            border: "none",
            cursor: "pointer",
          }}
        >
          Back to Contests
        </button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "24px 20px" }}>
      {/* Contest Banner / Top Bar */}
      <div
        style={{
          padding: 24,
          borderRadius: 12,
          backgroundColor: "var(--color-card-bg, #ffffff)",
          border: "1px solid var(--color-border, #e2e8f0)",
          marginBottom: 24,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 16,
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
            <span
              style={{
                fontSize: 12,
                fontWeight: 700,
                padding: "3px 10px",
                borderRadius: 9999,
                backgroundColor:
                  contest.status === "LIVE" ? "#fee2e2" : contest.status === "UPCOMING" ? "#e0f2fe" : "#f1f5f9",
                color:
                  contest.status === "LIVE" ? "#dc2626" : contest.status === "UPCOMING" ? "#0284c7" : "#475569",
              }}
            >
              {contest.status}
            </span>
            <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: "var(--color-text-primary, #0f172a)" }}>
              {contest.title}
            </h1>
          </div>
          <p style={{ margin: "0 0 12px 0", color: "var(--color-text-secondary, #64748b)", fontSize: 14 }}>
            {contest.description}
          </p>
          <div style={{ display: "flex", gap: 16, fontSize: 13, color: "var(--color-text-secondary, #64748b)" }}>
            <span>Participants: <strong>{contest.participant_count}</strong></span>
            {contest.is_registered && (
              <>
                <span>My Score: <strong>{contest.my_score} pts</strong></span>
                <span>Penalty: <strong>{contest.my_penalty} mins</strong></span>
                {contest.my_rank && <span>Current Rank: <strong>#{contest.my_rank}</strong></span>}
              </>
            )}
          </div>
        </div>

        {/* Timer & Registration Action */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 12 }}>
          {contest.status === "LIVE" && (
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 12, color: "#64748b", fontWeight: 600 }}>TIME REMAINING</div>
              <div style={{ fontSize: 28, fontWeight: 800, fontFamily: "monospace", color: "#dc2626" }}>
                {formatCountdown(remainingSec)}
              </div>
            </div>
          )}
          {contest.status === "UPCOMING" && (
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 12, color: "#64748b", fontWeight: 600 }}>STARTS IN</div>
              <div style={{ fontSize: 24, fontWeight: 700, fontFamily: "monospace", color: "#0284c7" }}>
                {formatCountdown(remainingSec)}
              </div>
            </div>
          )}

          {!contest.is_registered && contest.status !== "ENDED" && (
            <button
              onClick={handleRegister}
              style={{
                padding: "10px 20px",
                borderRadius: 8,
                backgroundColor: "var(--color-primary, #2563eb)",
                color: "#fff",
                fontWeight: 600,
                border: "none",
                cursor: "pointer",
              }}
            >
              Register Now
            </button>
          )}
          {contest.is_registered && (
            <span
              style={{
                padding: "6px 12px",
                borderRadius: 6,
                backgroundColor: "#ecfdf5",
                color: "#059669",
                fontWeight: 600,
                fontSize: 13,
                border: "1px solid #a7f3d0",
              }}
            >
              ✓ Registered
            </span>
          )}
        </div>
      </div>

      {actionNotice && (
        <div
          style={{
            padding: 12,
            marginBottom: 20,
            borderRadius: 8,
            backgroundColor: "#eff6ff",
            color: "#1d4ed8",
            border: "1px solid #bfdbfe",
          }}
        >
          {actionNotice}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: "flex", borderBottom: "1px solid var(--color-border, #e2e8f0)", marginBottom: 20, gap: 20 }}>
        <button
          onClick={() => setActiveTab("PROBLEMS")}
          style={{
            background: "none",
            border: "none",
            padding: "10px 4px",
            fontSize: 16,
            fontWeight: 600,
            cursor: "pointer",
            color: activeTab === "PROBLEMS" ? "var(--color-primary, #2563eb)" : "#64748b",
            borderBottom: activeTab === "PROBLEMS" ? "2px solid var(--color-primary, #2563eb)" : "2px solid transparent",
          }}
        >
          Problems ({contest.problems.length})
        </button>
        <button
          onClick={() => {
            setActiveTab("STANDINGS");
            fetchStandings();
          }}
          style={{
            background: "none",
            border: "none",
            padding: "10px 4px",
            fontSize: 16,
            fontWeight: 600,
            cursor: "pointer",
            color: activeTab === "STANDINGS" ? "var(--color-primary, #2563eb)" : "#64748b",
            borderBottom: activeTab === "STANDINGS" ? "2px solid var(--color-primary, #2563eb)" : "2px solid transparent",
          }}
        >
          Standings & Leaderboard
        </button>
      </div>

      {/* Tab: Problems */}
      {activeTab === "PROBLEMS" && (
        <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 24 }}>
          {/* Problem Selector Sidebar */}
          <div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {contest.problems.map((p, idx) => {
                const label = String.fromCharCode(65 + idx);
                const isSelected = selectedProblem?.id === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => setSelectedProblem(p)}
                    style={{
                      padding: "14px 16px",
                      borderRadius: 8,
                      border: isSelected ? "2px solid var(--color-primary, #2563eb)" : "1px solid var(--color-border, #e2e8f0)",
                      backgroundColor: isSelected ? "#eff6ff" : "var(--color-card-bg, #ffffff)",
                      cursor: "pointer",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <div>
                      <span style={{ fontWeight: 700, marginRight: 8, color: "#2563eb" }}>{label}.</span>
                      <span style={{ fontWeight: 600, color: "#1e293b" }}>{p.title}</span>
                      <div style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>
                        {p.points} pts • {p.difficulty}
                      </div>
                    </div>
                    {p.solved && (
                      <span style={{ color: "#059669", fontSize: 16, fontWeight: 700 }}>✓</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Active Problem Workspace */}
          {selectedProblem ? (
            <div
              style={{
                backgroundColor: "var(--color-card-bg, #ffffff)",
                padding: 24,
                borderRadius: 12,
                border: "1px solid var(--color-border, #e2e8f0)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                <div>
                  <h2 style={{ margin: "0 0 6px 0", fontSize: 20, color: "#0f172a" }}>
                    {selectedProblem.title}
                  </h2>
                  <div style={{ fontSize: 13, color: "#64748b" }}>
                    Score value: <strong>{selectedProblem.points} pts</strong> | Penalty per wrong attempt: <strong>{selectedProblem.penalty_minutes} mins</strong>
                  </div>
                </div>
                <button
                  onClick={() => onNavigate(`/problems/${selectedProblem.slug}`)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: 6,
                    border: "1px solid #cbd5e1",
                    backgroundColor: "#f8fafc",
                    fontSize: 13,
                    cursor: "pointer",
                  }}
                >
                  View Full Statement ↗
                </button>
              </div>

              {/* Code Submission Area */}
              <div style={{ marginTop: 20 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, alignItems: "center" }}>
                  <label style={{ fontSize: 14, fontWeight: 600, color: "#334155" }}>Solution Submission:</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    style={{
                      padding: "6px 10px",
                      borderRadius: 6,
                      border: "1px solid #cbd5e1",
                      backgroundColor: "#fff",
                      fontSize: 13,
                    }}
                  >
                    <option value="python">Python 3</option>
                    <option value="cpp">C++ 17</option>
                    <option value="java">Java 17</option>
                    <option value="javascript">JavaScript (Node.js)</option>
                  </select>
                </div>

                <textarea
                  value={sourceCode}
                  onChange={(e) => setSourceCode(e.target.value)}
                  rows={14}
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
                  }}
                />

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 12 }}>
                  <span style={{ fontSize: 12, color: "#94a3b8" }}>
                    🛡️ Anti-Cheat Active: Submissions throttled to 5s. Code similarity verified.
                  </span>
                  <button
                    onClick={handleSubmit}
                    disabled={submitting || contest.status !== "LIVE"}
                    style={{
                      padding: "10px 24px",
                      borderRadius: 8,
                      backgroundColor: contest.status === "LIVE" ? "var(--color-primary, #2563eb)" : "#94a3b8",
                      color: "#fff",
                      fontWeight: 600,
                      border: "none",
                      cursor: contest.status === "LIVE" ? "pointer" : "not-allowed",
                    }}
                  >
                    {submitting ? "Submitting..." : contest.status === "LIVE" ? "Submit to Online Judge" : "Contest Inactive"}
                  </button>
                </div>

                {submitResult && (
                  <div
                    style={{
                      marginTop: 16,
                      padding: 14,
                      borderRadius: 8,
                      backgroundColor: submitResult.verdict === "ACCEPTED" ? "#ecfdf5" : "#fef2f2",
                      border: `1px solid ${submitResult.verdict === "ACCEPTED" ? "#a7f3d0" : "#fecaca"}`,
                      color: submitResult.verdict === "ACCEPTED" ? "#065f46" : "#991b1b",
                    }}
                  >
                    <strong>Verdict: {submitResult.verdict}</strong> — {submitResult.message}
                    {submitResult.score > 0 && ` (Score: +${submitResult.score} pts)`}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div style={{ padding: 40, textAlign: "center", color: "#64748b" }}>
              Select a problem from the left panel to begin.
            </div>
          )}
        </div>
      )}

      {/* Tab: Standings */}
      {activeTab === "STANDINGS" && (
        <div
          style={{
            backgroundColor: "var(--color-card-bg, #ffffff)",
            padding: 24,
            borderRadius: 12,
            border: "1px solid var(--color-border, #e2e8f0)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ margin: 0, fontSize: 18, color: "#0f172a" }}>
              Live Scoreboard ({leaderboard?.total_participants || 0} competitors)
            </h3>
            <button
              onClick={fetchStandings}
              style={{
                padding: "6px 12px",
                borderRadius: 6,
                border: "1px solid #cbd5e1",
                backgroundColor: "#f8fafc",
                cursor: "pointer",
                fontSize: 13,
              }}
            >
              🔄 Refresh
            </button>
          </div>

          {!leaderboard || leaderboard.entries.length === 0 ? (
            <p style={{ textAlign: "center", color: "#64748b", padding: "30px 0" }}>
              No scores recorded yet. Submissions will populate here in real-time.
            </p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: 14 }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid #e2e8f0", color: "#64748b" }}>
                    <th style={{ padding: "10px 14px", width: 60 }}>Rank</th>
                    <th style={{ padding: "10px 14px" }}>Competitor</th>
                    <th style={{ padding: "10px 14px" }}>Score</th>
                    <th style={{ padding: "10px 14px" }}>Penalty</th>
                    <th style={{ padding: "10px 14px" }}>Solved</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.entries.map((entry) => (
                    <tr key={entry.rank + entry.display_name} style={{ borderBottom: "1px solid #e2e8f0" }}>
                      <td style={{ padding: "12px 14px", fontWeight: 700 }}>
                        {entry.rank === 1 ? "🥇 1" : entry.rank === 2 ? "🥈 2" : entry.rank === 3 ? "🥉 3" : `#${entry.rank}`}
                      </td>
                      <td style={{ padding: "12px 14px", fontWeight: 600, color: "#1e293b" }}>
                        {entry.display_name}
                      </td>
                      <td style={{ padding: "12px 14px", fontWeight: 700, color: "#2563eb" }}>
                        {entry.score}
                      </td>
                      <td style={{ padding: "12px 14px", color: "#64748b" }}>
                        {entry.penalty}m
                      </td>
                      <td style={{ padding: "12px 14px", fontWeight: 600 }}>
                        {entry.problems_solved} / {contest.problems.length}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
