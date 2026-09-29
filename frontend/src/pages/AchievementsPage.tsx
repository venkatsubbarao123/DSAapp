import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.tsx";
import { gamificationApi } from "../services/gamificationApi.ts";
import { AchievementsResponse } from "../types/gamification.ts";

interface AchievementsPageProps {
  onNavigate?: (path: string) => void;
}

const TIER_COLORS: Record<string, { border: string; bg: string; text: string }> = {
  BRONZE: { border: "#cd7f32", bg: "rgba(205, 127, 50, 0.15)", text: "#cd7f32" },
  SILVER: { border: "#c0c0c0", bg: "rgba(192, 192, 192, 0.15)", text: "#e0e0e0" },
  GOLD: { border: "#ffd700", bg: "rgba(255, 215, 0, 0.15)", text: "#ffd700" },
  PLATINUM: { border: "#00ffff", bg: "rgba(0, 255, 255, 0.15)", text: "#00ffff" },
};

export const AchievementsPage: React.FC<AchievementsPageProps> = ({ onNavigate: _onNavigate }) => {
  const { isAuthenticated, openAuthModal } = useAuth();

  const [data, setData] = useState<AchievementsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [tierFilter, setTierFilter] = useState<string>("ALL");
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    gamificationApi
      .getAchievements()
      .then(setData)
      .catch((err) => console.error("Could not load achievements", err))
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div style={{ maxWidth: "800px", margin: "0 auto", padding: "var(--space-12) var(--space-4)", textAlign: "center" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 800 }}>Achievements & Mastery Badges</h1>
        <p style={{ color: "var(--text-secondary)", marginTop: "var(--space-2)" }}>
          Sign in to track your milestone badges, streaks, and server-verified skill achievements.
        </p>
        <button
          onClick={() => openAuthModal("login")}
          style={{
            backgroundColor: "var(--brand-primary)",
            color: "#ffffff",
            border: "none",
            padding: "10px 24px",
            borderRadius: "var(--radius-md)",
            cursor: "pointer",
            fontWeight: 700,
            marginTop: "var(--space-4)",
          }}
        >
          Sign In to View Badges
        </button>
      </div>
    );
  }

  const filteredAchievements = data?.achievements.filter((ach) => {
    if (tierFilter !== "ALL" && ach.tier !== tierFilter) return false;
    if (categoryFilter !== "ALL" && ach.category !== categoryFilter) return false;
    return true;
  });

  const categories = Array.from(new Set(data?.achievements.map((a) => a.category) || []));

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "var(--space-8) var(--space-4)", width: "100%" }}>
      {/* Header */}
      <div style={{ marginBottom: "var(--space-8)" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: 0 }}>Achievements & Badges</h1>
        <p style={{ color: "var(--text-secondary)", marginTop: "var(--space-2)" }}>
          Earn XP and showcase your DSA problem-solving milestones.
        </p>

        {/* Progress summary banner */}
        {data && (
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-6)",
              marginTop: "var(--space-6)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-2)" }}>
              <span style={{ fontWeight: 700 }}>
                {data.unlocked_count} of {data.total_achievements} Badges Unlocked
              </span>
              <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--brand-primary)" }}>
                {Math.round((data.unlocked_count / (data.total_achievements || 1)) * 100)}%
              </span>
            </div>
            <div
              style={{
                height: "10px",
                backgroundColor: "var(--bg-tertiary)",
                borderRadius: "var(--radius-full)",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${(data.unlocked_count / (data.total_achievements || 1)) * 100}%`,
                  backgroundColor: "var(--brand-primary)",
                  borderRadius: "var(--radius-full)",
                  transition: "width 0.3s ease",
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Filter controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "var(--space-4)",
          marginBottom: "var(--space-6)",
        }}
      >
        {/* Tier filter */}
        <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
          {["ALL", "BRONZE", "SILVER", "GOLD", "PLATINUM"].map((tier) => (
            <button
              key={tier}
              onClick={() => setTierFilter(tier)}
              style={{
                backgroundColor: tierFilter === tier ? "var(--bg-tertiary)" : "var(--bg-secondary)",
                border: tierFilter === tier ? "1px solid var(--brand-primary)" : "1px solid var(--border-subtle)",
                color: tierFilter === tier ? "var(--text-primary)" : "var(--text-secondary)",
                fontSize: "0.75rem",
                fontWeight: 600,
                padding: "6px 12px",
                borderRadius: "var(--radius-md)",
                cursor: "pointer",
              }}
            >
              {tier}
            </button>
          ))}
        </div>

        {/* Category filter */}
        <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
          <button
            onClick={() => setCategoryFilter("ALL")}
            style={{
              backgroundColor: categoryFilter === "ALL" ? "var(--bg-tertiary)" : "var(--bg-secondary)",
              border: categoryFilter === "ALL" ? "1px solid var(--brand-primary)" : "1px solid var(--border-subtle)",
              color: categoryFilter === "ALL" ? "var(--text-primary)" : "var(--text-secondary)",
              fontSize: "0.75rem",
              fontWeight: 600,
              padding: "6px 12px",
              borderRadius: "var(--radius-md)",
              cursor: "pointer",
            }}
          >
            All Categories
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              style={{
                backgroundColor: categoryFilter === cat ? "var(--bg-tertiary)" : "var(--bg-secondary)",
                border: categoryFilter === cat ? "1px solid var(--brand-primary)" : "1px solid var(--border-subtle)",
                color: categoryFilter === cat ? "var(--text-primary)" : "var(--text-secondary)",
                fontSize: "0.75rem",
                fontWeight: 600,
                padding: "6px 12px",
                borderRadius: "var(--radius-md)",
                cursor: "pointer",
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Badges Grid */}
      {loading ? (
        <div style={{ textAlign: "center", padding: "var(--space-12)", color: "var(--text-muted)" }}>
          Loading achievements...
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            gap: "var(--space-4)",
          }}
        >
          {filteredAchievements?.map((ach) => {
            const tierStyle = TIER_COLORS[ach.tier] || TIER_COLORS.BRONZE;

            return (
              <div
                key={ach.id}
                style={{
                  backgroundColor: ach.unlocked ? "var(--bg-secondary)" : "rgba(30, 41, 59, 0.4)",
                  border: ach.unlocked
                    ? `2px solid ${tierStyle.border}`
                    : "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-lg)",
                  padding: "var(--space-5)",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  opacity: ach.unlocked ? 1 : 0.65,
                  boxShadow: ach.unlocked ? `0 0 12px ${tierStyle.bg}` : "none",
                  transition: "all 0.2s ease",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
                    <span
                      style={{
                        fontSize: "0.6875rem",
                        fontWeight: 700,
                        padding: "2px 8px",
                        borderRadius: "var(--radius-sm)",
                        backgroundColor: tierStyle.bg,
                        color: tierStyle.text,
                        border: `1px solid ${tierStyle.border}`,
                      }}
                    >
                      {ach.tier}
                    </span>
                    <span
                      style={{
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        color: "var(--brand-primary)",
                      }}
                    >
                      +{ach.xp_reward} XP
                    </span>
                  </div>

                  <h3 style={{ fontSize: "1.125rem", fontWeight: 700, margin: "0 0 6px 0" }}>
                    {ach.unlocked ? "🏆 " : "🔒 "}
                    {ach.name}
                  </h3>
                  <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", margin: 0, lineHeight: 1.4 }}>
                    {ach.description}
                  </p>
                </div>

                <div style={{ marginTop: "var(--space-4)", borderTop: "1px solid var(--border-subtle)", paddingTop: "var(--space-3)" }}>
                  {ach.unlocked ? (
                    <div style={{ fontSize: "0.75rem", color: "var(--status-success)", fontWeight: 600 }}>
                      ✓ Unlocked {ach.unlocked_at ? new Date(ach.unlocked_at).toLocaleDateString() : ""}
                    </div>
                  ) : (
                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.6875rem", color: "var(--text-muted)", marginBottom: "4px" }}>
                        <span>Progress</span>
                        <span>
                          {ach.progress_value} / {ach.target_value}
                        </span>
                      </div>
                      <div
                        style={{
                          height: "6px",
                          backgroundColor: "var(--bg-tertiary)",
                          borderRadius: "var(--radius-full)",
                          overflow: "hidden",
                        }}
                      >
                        <div
                          style={{
                            height: "100%",
                            width: `${Math.min(ach.progress_percent, 100)}%`,
                            backgroundColor: "var(--text-muted)",
                            borderRadius: "var(--radius-full)",
                          }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
