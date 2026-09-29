import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.tsx";
import { cpApi } from "../services/cpApi.ts";
import {
  CPProblem,
  UserCPRating,
  CPLeaderboardEntry,
  CPRatingBand,
} from "../types/cp.ts";

interface CompetitivePageProps {
  onNavigate: (path: string) => void;
}

export const CompetitivePage: React.FC<CompetitivePageProps> = ({ onNavigate }) => {
  const { isAuthenticated } = useAuth();

  const [activeTab, setActiveTab] = useState<"PROBLEMS" | "LEADERBOARD">("PROBLEMS");
  const [ratingBands, setRatingBands] = useState<CPRatingBand[]>([]);
  const [selectedBand, setSelectedBand] = useState<string>("ALL");
  const [problems, setProblems] = useState<CPProblem[]>([]);
  const [myRating, setMyRating] = useState<UserCPRating | null>(null);
  const [leaderboard, setLeaderboard] = useState<CPLeaderboardEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const [bands, probs, lb] = await Promise.all([
        cpApi.getBands(),
        cpApi.getProblems(selectedBand !== "ALL" ? { rating_band: selectedBand } : undefined),
        cpApi.getLeaderboard(25),
      ]);
      setRatingBands(bands);
      setProblems(probs);
      setLeaderboard(lb);

      if (isAuthenticated) {
        try {
          const ratingData = await cpApi.getMyRating();
          setMyRating(ratingData);
        } catch {
          // May not have rated history yet
        }
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to load competitive programming data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedBand, isAuthenticated]);

  const getBandBadgeStyle = (band: string) => {
    switch (band) {
      case "DIV_1":
        return { bg: "#fee2e2", text: "#dc2626", border: "#fecaca" };
      case "DIV_2":
        return { bg: "#fef3c7", text: "#d97706", border: "#fde68a" };
      case "DIV_3":
        return { bg: "#dbeafe", text: "#2563eb", border: "#bfdbfe" };
      default:
        return { bg: "#f1f5f9", text: "#475569", border: "#e2e8f0" };
    }
  };

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "32px 20px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 32, flexWrap: "wrap", gap: 16 }}>
        <div>
          <h1 style={{ margin: "0 0 8px 0", fontSize: 28, fontWeight: 700, color: "#0f172a" }}>
            ⚔️ Competitive Programming Ladder
          </h1>
          <p style={{ margin: 0, color: "#64748b", fontSize: 16 }}>
            Curated problems grouped by Codeforces rating bands (800 – 2400+) with Elo-based competitive rating tracking.
          </p>
        </div>

        <button
          onClick={() => onNavigate("/contests")}
          style={{
            padding: "10px 18px",
            borderRadius: 8,
            backgroundColor: "#2563eb",
            color: "#ffffff",
            fontWeight: 600,
            border: "none",
            cursor: "pointer",
          }}
        >
          🏆 Live Arena Contests →
        </button>
      </div>

      {/* User Competitive Rating Hero Card */}
      {isAuthenticated && myRating && (
        <div
          style={{
            padding: 24,
            borderRadius: 12,
            backgroundColor: "#ffffff",
            border: "1px solid #e2e8f0",
            marginBottom: 32,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 20,
          }}
        >
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>
              Competitive Rating Profile
            </div>
            <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginTop: 4 }}>
              <span style={{ fontSize: 32, fontWeight: 800, color: "#0f172a" }}>
                {myRating.current_rating}
              </span>
              <span
                style={{
                  fontSize: 13,
                  fontWeight: 700,
                  padding: "2px 10px",
                  borderRadius: 9999,
                  ...getBandBadgeStyle(myRating.rating_band),
                }}
              >
                {myRating.rank_title}
              </span>
            </div>
            <div style={{ fontSize: 13, color: "#64748b", marginTop: 6 }}>
              Peak Rating: <strong>{myRating.max_rating}</strong> • Rated Contests: <strong>{myRating.contests_attended}</strong>
            </div>
          </div>

          {/* Recent Rating History preview */}
          {myRating.history && myRating.history.length > 0 && (
            <div style={{ display: "flex", gap: 16 }}>
              {myRating.history.slice(-3).map((h) => (
                <div
                  key={h.contest_id}
                  style={{
                    padding: "8px 14px",
                    borderRadius: 8,
                    backgroundColor: "#f8fafc",
                    border: "1px solid #e2e8f0",
                    fontSize: 12,
                  }}
                >
                  <div style={{ fontWeight: 600, color: "#1e293b", maxWidth: 120, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                    {h.contest_title}
                  </div>
                  <div style={{ color: h.rating_change >= 0 ? "#16a34a" : "#dc2626", fontWeight: 700 }}>
                    {h.rating_change >= 0 ? `+${h.rating_change}` : h.rating_change} (→ {h.rating_after})
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: "flex", borderBottom: "1px solid #e2e8f0", marginBottom: 24, gap: 24 }}>
        <button
          onClick={() => setActiveTab("PROBLEMS")}
          style={{
            background: "none",
            border: "none",
            padding: "10px 4px",
            fontSize: 15,
            fontWeight: 600,
            cursor: "pointer",
            color: activeTab === "PROBLEMS" ? "#2563eb" : "#64748b",
            borderBottom: activeTab === "PROBLEMS" ? "2px solid #2563eb" : "2px solid transparent",
          }}
        >
          Rating Bands & Problems
        </button>
        <button
          onClick={() => setActiveTab("LEADERBOARD")}
          style={{
            background: "none",
            border: "none",
            padding: "10px 4px",
            fontSize: 15,
            fontWeight: 600,
            cursor: "pointer",
            color: activeTab === "LEADERBOARD" ? "#2563eb" : "#64748b",
            borderBottom: activeTab === "LEADERBOARD" ? "2px solid #2563eb" : "2px solid transparent",
          }}
        >
          Global Competitive Leaderboard
        </button>
      </div>

      {errorMsg && (
        <div style={{ padding: 14, borderRadius: 8, backgroundColor: "#fef2f2", color: "#991b1b", marginBottom: 24 }}>
          {errorMsg}
        </div>
      )}

      {/* Tab: Problems */}
      {activeTab === "PROBLEMS" && (
        <div>
          {/* Rating Band Filters */}
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 24 }}>
            <button
              onClick={() => setSelectedBand("ALL")}
              style={{
                padding: "8px 16px",
                borderRadius: 8,
                border: "1px solid #cbd5e1",
                backgroundColor: selectedBand === "ALL" ? "#2563eb" : "#ffffff",
                color: selectedBand === "ALL" ? "#ffffff" : "#334155",
                fontWeight: 600,
                fontSize: 13,
                cursor: "pointer",
              }}
            >
              All Bands
            </button>
            {ratingBands.map((band) => (
              <button
                key={band.name}
                onClick={() => setSelectedBand(band.name)}
                style={{
                  padding: "8px 16px",
                  borderRadius: 8,
                  border: "1px solid #cbd5e1",
                  backgroundColor: selectedBand === band.name ? "#2563eb" : "#ffffff",
                  color: selectedBand === band.name ? "#ffffff" : "#334155",
                  fontWeight: 600,
                  fontSize: 13,
                  cursor: "pointer",
                }}
              >
                {band.name.replace("_", " ")} ({band.min_rating} – {band.max_rating})
              </button>
            ))}
          </div>

          {loading ? (
            <div style={{ textAlign: "center", padding: 40, color: "#64748b" }}>Loading problem ladder...</div>
          ) : problems.length === 0 ? (
            <div style={{ textAlign: "center", padding: 40, color: "#64748b", border: "1px dashed #cbd5e1", borderRadius: 8 }}>
              No competitive problems registered in this rating band yet.
            </div>
          ) : (
            <div style={{ display: "grid", gap: 12 }}>
              {problems.map((p) => {
                const badgeStyle = getBandBadgeStyle(p.rating_band);
                return (
                  <div
                    key={p.id}
                    onClick={() => onNavigate(`/problems/${p.slug}`)}
                    style={{
                      padding: "16px 20px",
                      borderRadius: 10,
                      backgroundColor: "#ffffff",
                      border: "1px solid #e2e8f0",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      cursor: "pointer",
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                        <span style={{ fontWeight: 600, color: "#0f172a", fontSize: 16 }}>
                          {p.title}
                        </span>
                        <span
                          style={{
                            fontSize: 11,
                            fontWeight: 700,
                            padding: "2px 8px",
                            borderRadius: 4,
                            ...badgeStyle,
                          }}
                        >
                          ★ {p.rating}
                        </span>
                        {p.platform && (
                          <span style={{ fontSize: 11, color: "#64748b", backgroundColor: "#f1f5f9", padding: "1px 6px", borderRadius: 4 }}>
                            {p.platform} {p.cf_contest_id ? `${p.cf_contest_id}${p.cf_index}` : ""}
                          </span>
                        )}
                      </div>

                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6 }}>
                        {p.tags.map((tag) => (
                          <span
                            key={tag}
                            style={{
                              fontSize: 11,
                              padding: "1px 6px",
                              borderRadius: 4,
                              backgroundColor: "#f8fafc",
                              color: "#64748b",
                              border: "1px solid #e2e8f0",
                            }}
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                      <span style={{ fontSize: 13, color: "#64748b" }}>
                        Solved by: <strong>{p.solved_count}</strong>
                      </span>
                      {p.solved_by_user && (
                        <span style={{ color: "#16a34a", fontWeight: 700 }}>✓ Solved</span>
                      )}
                      <span style={{ color: "#2563eb", fontWeight: 600 }}>Solve →</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab: Leaderboard */}
      {activeTab === "LEADERBOARD" && (
        <div
          style={{
            backgroundColor: "#ffffff",
            padding: 24,
            borderRadius: 12,
            border: "1px solid #e2e8f0",
          }}
        >
          <h3 style={{ margin: "0 0 16px 0", fontSize: 18, color: "#0f172a" }}>
            Top Rated Competitors
          </h3>

          {leaderboard.length === 0 ? (
            <p style={{ textAlign: "center", color: "#64748b", padding: 30 }}>
              No competitive rankings established yet. Compete in live rounds to rank!
            </p>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: "2px solid #e2e8f0", color: "#64748b" }}>
                  <th style={{ padding: "10px 14px", width: 60 }}>Rank</th>
                  <th style={{ padding: "10px 14px" }}>Handle</th>
                  <th style={{ padding: "10px 14px" }}>Rating</th>
                  <th style={{ padding: "10px 14px" }}>Title</th>
                  <th style={{ padding: "10px 14px" }}>Rounds</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((u) => (
                  <tr key={u.user_id} style={{ borderBottom: "1px solid #e2e8f0" }}>
                    <td style={{ padding: "12px 14px", fontWeight: 700 }}>
                      {u.rank === 1 ? "🥇 1" : u.rank === 2 ? "🥈 2" : u.rank === 3 ? "🥉 3" : `#${u.rank}`}
                    </td>
                    <td style={{ padding: "12px 14px", fontWeight: 600, color: "#0f172a" }}>
                      {u.display_name}
                    </td>
                    <td style={{ padding: "12px 14px", fontWeight: 700, color: "#2563eb" }}>
                      {u.current_rating}
                    </td>
                    <td style={{ padding: "12px 14px", color: "#64748b" }}>
                      {u.rank_title}
                    </td>
                    <td style={{ padding: "12px 14px", color: "#64748b" }}>
                      {u.contests_attended}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};
