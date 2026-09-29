import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.tsx";
import { contestApi } from "../services/contestApi.ts";
import { ContestSummary, UserContestHistory } from "../types/contest.ts";

interface ContestsPageProps {
  onNavigate: (path: string) => void;
}

export const ContestsPage: React.FC<ContestsPageProps> = ({ onNavigate }) => {
  const { isAuthenticated, openAuthModal } = useAuth();

  const [activeTab, setActiveTab] = useState<"LIVE" | "UPCOMING" | "PAST" | "HISTORY">("LIVE");
  const [contests, setContests] = useState<ContestSummary[]>([]);
  const [history, setHistory] = useState<UserContestHistory[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadContests = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      if (activeTab === "HISTORY") {
        if (isAuthenticated) {
          const hist = await contestApi.getMyContestHistory();
          setHistory(hist);
        } else {
          setHistory([]);
        }
      } else {
        const statusFilter = activeTab === "LIVE" ? "LIVE" : activeTab === "UPCOMING" ? "UPCOMING" : "ENDED";
        const data = await contestApi.getContests(statusFilter);
        setContests(data);
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to load contests");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadContests();
  }, [activeTab, isAuthenticated]);

  const handleRegister = async (slug: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isAuthenticated) {
      openAuthModal("login");
      return;
    }
    try {
      const res = await contestApi.registerForContest(slug);
      setActionMessage(res.message);
      setTimeout(() => setActionMessage(null), 4000);
      loadContests();
    } catch (err: unknown) {
      setActionMessage(err instanceof Error ? err.message : "Registration failed");
    }
  };

  const formatCountdown = (seconds: number) => {
    if (seconds <= 0) return "Started";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h}h ${m}m ${s}s`;
  };

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "32px 20px" }}>
      {/* Page Header */}
      <div style={{ marginBottom: 32, display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
        <div>
          <h1 style={{ margin: "0 0 8px 0", fontSize: 28, fontWeight: 700, color: "var(--color-text-primary, #1e293b)" }}>
            🏆 Competitive Arena & Contests
          </h1>
          <p style={{ margin: 0, color: "var(--color-text-secondary, #64748b)", fontSize: 16 }}>
            Compete in real-time rating-rated rounds under ICPC rules with zero-latency live scoreboards.
          </p>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <button
            onClick={() => onNavigate("/competitive")}
            style={{
              padding: "10px 18px",
              borderRadius: 8,
              border: "1px solid var(--color-border, #cbd5e1)",
              backgroundColor: "transparent",
              color: "var(--color-text-primary, #334155)",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            📊 Rating Ladders
          </button>
        </div>
      </div>

      {actionMessage && (
        <div
          style={{
            padding: "12px 16px",
            marginBottom: 20,
            borderRadius: 8,
            backgroundColor: "#eff6ff",
            border: "1px solid #bfdbfe",
            color: "#1d4ed8",
            fontWeight: 500,
          }}
        >
          ℹ️ {actionMessage}
        </div>
      )}

      {/* Navigation Tabs */}
      <div
        style={{
          display: "flex",
          borderBottom: "1px solid var(--color-border, #e2e8f0)",
          marginBottom: 24,
          gap: 24,
        }}
      >
        {(["LIVE", "UPCOMING", "PAST", "HISTORY"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              background: "none",
              border: "none",
              padding: "12px 4px",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: 15,
              color: activeTab === tab ? "var(--color-primary, #2563eb)" : "var(--color-text-secondary, #64748b)",
              borderBottom: activeTab === tab ? "2px solid var(--color-primary, #2563eb)" : "2px solid transparent",
              transition: "all 0.2s ease",
            }}
          >
            {tab === "LIVE" && "🔴 Live Now"}
            {tab === "UPCOMING" && "⏳ Upcoming Contests"}
            {tab === "PAST" && "📜 Past Contests"}
            {tab === "HISTORY" && "👤 My Contests"}
          </button>
        ))}
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div style={{ padding: "60px 0", textAlign: "center", color: "var(--color-text-secondary, #64748b)" }}>
          Loading arena data...
        </div>
      )}

      {errorMsg && (
        <div
          style={{
            padding: 16,
            borderRadius: 8,
            backgroundColor: "#fef2f2",
            color: "#b91c1c",
            marginBottom: 24,
            border: "1px solid #fecaca",
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* Contests List */}
      {!loading && !errorMsg && activeTab !== "HISTORY" && (
        <div>
          {contests.length === 0 ? (
            <div
              style={{
                padding: "48px 24px",
                textAlign: "center",
                borderRadius: 12,
                backgroundColor: "var(--color-bg-secondary, #f8fafc)",
                border: "1px dashed var(--color-border, #cbd5e1)",
              }}
            >
              <p style={{ margin: "0 0 8px 0", fontSize: 18, fontWeight: 600, color: "var(--color-text-primary, #334155)" }}>
                No {activeTab.toLowerCase()} contests found
              </p>
              <p style={{ margin: 0, color: "var(--color-text-secondary, #64748b)" }}>
                Check back soon or explore practice problems in the problem set.
              </p>
            </div>
          ) : (
            <div style={{ display: "grid", gap: 16 }}>
              {contests.map((c) => (
                <div
                  key={c.id}
                  onClick={() => onNavigate(`/contests/${c.slug}`)}
                  style={{
                    padding: 20,
                    borderRadius: 12,
                    border: "1px solid var(--color-border, #e2e8f0)",
                    backgroundColor: "var(--color-card-bg, #ffffff)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    cursor: "pointer",
                    transition: "box-shadow 0.2s ease, transform 0.1s ease",
                  }}
                >
                  <div style={{ flex: 1, paddingRight: 20 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                      <span
                        style={{
                          fontSize: 12,
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: 9999,
                          backgroundColor:
                            c.status === "LIVE" ? "#fee2e2" : c.status === "UPCOMING" ? "#e0f2fe" : "#f1f5f9",
                          color:
                            c.status === "LIVE" ? "#dc2626" : c.status === "UPCOMING" ? "#0284c7" : "#475569",
                        }}
                      >
                        {c.status}
                      </span>
                      {c.premium_required && (
                        <span
                          style={{
                            fontSize: 12,
                            fontWeight: 700,
                            padding: "2px 8px",
                            borderRadius: 9999,
                            backgroundColor: "#fef3c7",
                            color: "#b45309",
                          }}
                        >
                          PRO
                        </span>
                      )}
                      <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: "var(--color-text-primary, #0f172a)" }}>
                        {c.title}
                      </h3>
                    </div>

                    <p style={{ margin: "0 0 10px 0", color: "var(--color-text-secondary, #64748b)", fontSize: 14 }}>
                      {c.description || "Official competitive challenge with automated ICPC verification."}
                    </p>

                    <div style={{ display: "flex", gap: 20, fontSize: 13, color: "var(--color-text-tertiary, #94a3b8)" }}>
                      <span>⏱️ Duration: {Math.round(c.duration_seconds / 60)} mins</span>
                      <span>👥 Participants: {c.participant_count}</span>
                      <span>📅 Start: {new Date(c.start_at).toLocaleString()}</span>
                    </div>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
                    {c.status === "UPCOMING" && (
                      <span style={{ fontSize: 13, fontWeight: 600, color: "#0284c7" }}>
                        Starts in: {formatCountdown(c.remaining_seconds)}
                      </span>
                    )}
                    {c.status === "LIVE" && (
                      <span style={{ fontSize: 13, fontWeight: 600, color: "#dc2626" }}>
                        Remaining: {formatCountdown(c.remaining_seconds)}
                      </span>
                    )}

                    <div style={{ display: "flex", gap: 8 }}>
                      {c.status === "UPCOMING" && (
                        <button
                          onClick={(e) => handleRegister(c.slug, e)}
                          style={{
                            padding: "8px 16px",
                            borderRadius: 6,
                            border: "none",
                            backgroundColor: "var(--color-primary, #2563eb)",
                            color: "#ffffff",
                            fontWeight: 600,
                            cursor: "pointer",
                          }}
                        >
                          Register
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onNavigate(`/contests/${c.slug}`);
                        }}
                        style={{
                          padding: "8px 16px",
                          borderRadius: 6,
                          border: "1px solid var(--color-border, #cbd5e1)",
                          backgroundColor: "#f8fafc",
                          color: "var(--color-text-primary, #1e293b)",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        Enter Arena →
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* User History Tab */}
      {!loading && !errorMsg && activeTab === "HISTORY" && (
        <div>
          {!isAuthenticated ? (
            <div style={{ textAlign: "center", padding: "40px 0" }}>
              <p style={{ marginBottom: 16, color: "var(--color-text-secondary, #64748b)" }}>
                Sign in to view your competition records and performance ratings.
              </p>
              <button
                onClick={() => openAuthModal("login")}
                style={{
                  padding: "10px 24px",
                  borderRadius: 8,
                  backgroundColor: "var(--color-primary, #2563eb)",
                  color: "#fff",
                  border: "none",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Sign In
              </button>
            </div>
          ) : history.length === 0 ? (
            <div
              style={{
                padding: "48px 24px",
                textAlign: "center",
                borderRadius: 12,
                backgroundColor: "var(--color-bg-secondary, #f8fafc)",
                border: "1px dashed var(--color-border, #cbd5e1)",
              }}
            >
              <p style={{ margin: "0 0 8px 0", fontSize: 18, fontWeight: 600, color: "var(--color-text-primary, #334155)" }}>
                No contest participations yet
              </p>
              <p style={{ margin: 0, color: "var(--color-text-secondary, #64748b)" }}>
                Join an upcoming contest to build your competitive rating!
              </p>
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid var(--color-border, #e2e8f0)", color: "#64748b", fontSize: 14 }}>
                    <th style={{ padding: "12px 16px" }}>Contest</th>
                    <th style={{ padding: "12px 16px" }}>Date</th>
                    <th style={{ padding: "12px 16px" }}>Score</th>
                    <th style={{ padding: "12px 16px" }}>Penalty</th>
                    <th style={{ padding: "12px 16px" }}>Rank</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <tr
                      key={h.contest_id}
                      onClick={() => onNavigate(`/contests/${h.contest_slug}`)}
                      style={{
                        borderBottom: "1px solid var(--color-border, #e2e8f0)",
                        cursor: "pointer",
                        fontSize: 14,
                      }}
                    >
                      <td style={{ padding: "14px 16px", fontWeight: 600, color: "var(--color-primary, #2563eb)" }}>
                        {h.contest_title}
                      </td>
                      <td style={{ padding: "14px 16px", color: "#64748b" }}>
                        {new Date(h.joined_at).toLocaleDateString()}
                      </td>
                      <td style={{ padding: "14px 16px", fontWeight: 600 }}>{h.final_score}</td>
                      <td style={{ padding: "14px 16px", color: "#64748b" }}>{h.final_penalty}m</td>
                      <td style={{ padding: "14px 16px", fontWeight: 600 }}>
                        {h.final_rank ? `#${h.final_rank} / ${h.total_participants}` : "Pending"}
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
