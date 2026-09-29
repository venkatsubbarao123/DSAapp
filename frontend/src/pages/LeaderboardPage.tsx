import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.tsx";
import { gamificationApi } from "../services/gamificationApi.ts";
import { LeaderboardEntry, LeaderboardResponse } from "../types/gamification.ts";

interface LeaderboardPageProps {
  onNavigate?: (path: string) => void;
}

type LeaderboardCategory = "weekly_xp" | "monthly_xp" | "all_time_xp" | "weekly_solves" | "streak";

const CATEGORIES: { id: LeaderboardCategory; label: string; icon: string; scoreUnit: string }[] = [
  { id: "weekly_xp", label: "Weekly XP", icon: "⚡", scoreUnit: "XP" },
  { id: "monthly_xp", label: "Monthly XP", icon: "📅", scoreUnit: "XP" },
  { id: "all_time_xp", label: "All-Time XP", icon: "👑", scoreUnit: "XP" },
  { id: "weekly_solves", label: "Weekly Solves", icon: "✓", scoreUnit: "Solves" },
  { id: "streak", label: "Longest Streak", icon: "🔥", scoreUnit: "Days" },
];

export const LeaderboardPage: React.FC<LeaderboardPageProps> = ({ onNavigate: _onNavigate }) => {
  const { user, isAuthenticated } = useAuth();

  const [category, setCategory] = useState<LeaderboardCategory>("weekly_xp");
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [userRanks, setUserRanks] = useState<Record<string, LeaderboardEntry>>({});
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    setLoading(true);
    gamificationApi
      .getLeaderboard(category, 50, 0)
      .then(setData)
      .catch((err) => console.error("Could not load leaderboard", err))
      .finally(() => setLoading(false));

    if (isAuthenticated) {
      gamificationApi
        .getUserRank()
        .then(setUserRanks)
        .catch(() => {});
    }
  }, [category, isAuthenticated]);

  const currentUnit = CATEGORIES.find((c) => c.id === category)?.scoreUnit || "XP";
  const currentUserEntry = userRanks[category];

  return (
    <div style={{ maxWidth: "900px", margin: "0 auto", padding: "var(--space-8) var(--space-4)", width: "100%" }}>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: "var(--space-8)" }}>
        <h1 style={{ fontSize: "2.25rem", fontWeight: 800, margin: 0 }}>Community Leaderboards</h1>
        <p style={{ color: "var(--text-secondary)", marginTop: "var(--space-2)" }}>
          Compete with peers on server-verified algorithmic problem solving, consistency, and XP.
        </p>

        {/* Current user rank banner */}
        {isAuthenticated && currentUserEntry && (
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--brand-primary)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-4) var(--space-6)",
              marginTop: "var(--space-6)",
              display: "inline-flex",
              alignItems: "center",
              gap: "var(--space-6)",
              boxShadow: "0 0 16px rgba(59, 130, 246, 0.15)",
            }}
          >
            <div>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Your Rank</span>
              <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--brand-primary)" }}>
                #{currentUserEntry.rank}
              </div>
            </div>
            <div style={{ borderLeft: "1px solid var(--border-subtle)", paddingLeft: "var(--space-6)" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Your Score</span>
              <div style={{ fontSize: "1.25rem", fontWeight: 800 }}>
                {currentUserEntry.score.toLocaleString()} {currentUnit}
              </div>
            </div>
            <div style={{ borderLeft: "1px solid var(--border-subtle)", paddingLeft: "var(--space-6)" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Level</span>
              <div style={{ fontSize: "1.25rem", fontWeight: 800 }}>
                Lv {currentUserEntry.current_level}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Category selector */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "var(--space-2)",
          flexWrap: "wrap",
          marginBottom: "var(--space-8)",
        }}
      >
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setCategory(cat.id)}
            style={{
              backgroundColor: category === cat.id ? "var(--brand-primary)" : "var(--bg-secondary)",
              color: category === cat.id ? "#ffffff" : "var(--text-secondary)",
              border: "1px solid var(--border-subtle)",
              padding: "8px 18px",
              borderRadius: "var(--radius-md)",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "0.875rem",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              transition: "all 0.15s ease",
            }}
          >
            <span>{cat.icon}</span>
            <span>{cat.label}</span>
          </button>
        ))}
      </div>

      {/* Leaderboard Table */}
      {loading ? (
        <div style={{ textAlign: "center", padding: "var(--space-12)", color: "var(--text-muted)" }}>
          Loading leaderboard rankings...
        </div>
      ) : data?.entries.length === 0 ? (
        <div style={{ textAlign: "center", padding: "var(--space-12)", color: "var(--text-muted)" }}>
          No entries recorded in this timeframe yet. Be the first to solve a problem!
        </div>
      ) : (
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
                <th style={{ padding: "12px 20px", width: "80px" }}>Rank</th>
                <th style={{ padding: "12px 20px" }}>Solver</th>
                <th style={{ padding: "12px 20px", width: "120px" }}>Level</th>
                <th style={{ padding: "12px 20px", width: "100px" }}>Streak</th>
                <th style={{ padding: "12px 20px", textAlign: "right", width: "140px" }}>{currentUnit}</th>
              </tr>
            </thead>
            <tbody>
              {data?.entries.map((entry) => {
                const isMe = user?.id === entry.user_id;

                let rankBadge = `#${entry.rank}`;
                let rankColor = "var(--text-muted)";
                if (entry.rank === 1) {
                  rankBadge = "🥇 1";
                  rankColor = "#ffd700";
                } else if (entry.rank === 2) {
                  rankBadge = "🥈 2";
                  rankColor = "#c0c0c0";
                } else if (entry.rank === 3) {
                  rankBadge = "🥉 3";
                  rankColor = "#cd7f32";
                }

                return (
                  <tr
                    key={entry.user_id}
                    style={{
                      borderBottom: "1px solid var(--border-subtle)",
                      backgroundColor: isMe ? "rgba(59, 130, 246, 0.08)" : "transparent",
                    }}
                  >
                    <td style={{ padding: "14px 20px", fontWeight: 700, color: rankColor, fontSize: "1rem" }}>
                      {rankBadge}
                    </td>
                    <td style={{ padding: "14px 20px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <div
                          style={{
                            width: "32px",
                            height: "32px",
                            borderRadius: "var(--radius-full)",
                            backgroundColor: "var(--bg-tertiary)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontWeight: 700,
                            fontSize: "0.8125rem",
                            border: "1px solid var(--border-muted)",
                          }}
                        >
                          {entry.display_name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div style={{ fontWeight: 600, color: isMe ? "var(--brand-primary)" : "var(--text-primary)" }}>
                            {entry.display_name} {isMe && "(You)"}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: "14px 20px" }}>
                      <span
                        style={{
                          fontSize: "0.75rem",
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: "var(--radius-sm)",
                          backgroundColor: "var(--bg-tertiary)",
                          border: "1px solid var(--border-muted)",
                        }}
                      >
                        Lv {entry.current_level}
                      </span>
                    </td>
                    <td style={{ padding: "14px 20px", fontWeight: 600 }}>
                      {entry.current_streak > 0 ? `🔥 ${entry.current_streak}d` : "—"}
                    </td>
                    <td
                      style={{
                        padding: "14px 20px",
                        textAlign: "right",
                        fontWeight: 700,
                        color: "var(--brand-primary)",
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.9375rem",
                      }}
                    >
                      {entry.score.toLocaleString()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
