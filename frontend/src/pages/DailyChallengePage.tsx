import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.tsx";
import { gamificationApi } from "../services/gamificationApi.ts";
import { DailyChallengeData, UserGamificationProfile } from "../types/gamification.ts";

interface DailyChallengePageProps {
  onNavigate: (path: string) => void;
}

export const DailyChallengePage: React.FC<DailyChallengePageProps> = ({ onNavigate }) => {
  const { isAuthenticated, openAuthModal } = useAuth();

  const [challenge, setChallenge] = useState<DailyChallengeData | null>(null);
  const [profile, setProfile] = useState<UserGamificationProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [claiming, setClaiming] = useState<boolean>(false);
  const [claimSuccessMsg, setClaimSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const challengeData = await gamificationApi.getDailyChallenge();
      setChallenge(challengeData);

      if (isAuthenticated) {
        const prof = await gamificationApi.getUserProfile();
        setProfile(prof);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load Daily Challenge.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [isAuthenticated]);

  const handleClaim = async () => {
    if (!isAuthenticated) {
      openAuthModal("login");
      return;
    }

    setClaiming(true);
    setErrorMsg(null);
    try {
      const res = await gamificationApi.claimDailyReward();
      setClaimSuccessMsg(res.message);
      // Reload state
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to claim Daily Challenge reward.");
    } finally {
      setClaiming(false);
    }
  };

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: "var(--space-8) var(--space-4)", width: "100%" }}>
      <div style={{ textAlign: "center", marginBottom: "var(--space-8)" }}>
        <span
          style={{
            fontSize: "0.8125rem",
            fontWeight: 700,
            color: "var(--brand-primary)",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          Daily Challenge
        </span>
        <h1 style={{ fontSize: "2.25rem", fontWeight: 800, margin: "var(--space-2) 0" }}>
          Solve Today's Problem
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "1rem" }}>
          Keep your problem-solving momentum alive. A new challenge unlocks every day at 00:00 UTC.
        </p>

        {profile && (
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "var(--space-4)",
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-full)",
              padding: "6px 18px",
              marginTop: "var(--space-3)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontWeight: 700 }}>
              <span style={{ fontSize: "1.25rem" }}>🔥</span>
              <span>{profile.current_streak} Day Streak</span>
            </div>
            <span style={{ color: "var(--border-subtle)" }}>|</span>
            <div style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>
              {profile.streak_freeze_count > 0 ? `🛡️ ${profile.streak_freeze_count} Freeze Active` : "No Freezes"}
            </div>
          </div>
        )}
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

      {claimSuccessMsg && (
        <div
          style={{
            backgroundColor: "rgba(16, 185, 129, 0.1)",
            color: "var(--status-success)",
            padding: "var(--space-4)",
            borderRadius: "var(--radius-md)",
            marginBottom: "var(--space-6)",
            border: "1px solid var(--status-success)",
            textAlign: "center",
            fontWeight: 600,
          }}
        >
          🎉 {claimSuccessMsg}
        </div>
      )}

      {loading && !challenge ? (
        <div style={{ textAlign: "center", padding: "var(--space-12)", color: "var(--text-muted)" }}>
          Loading daily challenge...
        </div>
      ) : challenge ? (
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-xl)",
            padding: "var(--space-8)",
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.2)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.875rem",
                color: "var(--text-muted)",
              }}
            >
              📅 {challenge.challenge_date}
            </span>
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 700,
                padding: "2px 10px",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-muted)",
              }}
            >
              {challenge.difficulty}
            </span>
          </div>

          <h2 style={{ fontSize: "1.5rem", fontWeight: 700, margin: "0 0 var(--space-4) 0" }}>
            {challenge.problem_title}
          </h2>

          {/* Reward Breakdown Cards */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "var(--space-4)",
              margin: "var(--space-6) 0",
            }}
          >
            <div
              style={{
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                padding: "var(--space-4)",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--brand-primary)" }}>
                +{challenge.xp_reward} XP
              </div>
              <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginTop: "4px" }}>
                Base Solve Reward
              </div>
            </div>

            <div
              style={{
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                padding: "var(--space-4)",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--status-warning)" }}>
                +{challenge.bonus_xp} XP
              </div>
              <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginTop: "4px" }}>
                First-Attempt Bonus
              </div>
            </div>
          </div>

          {/* Status and Action */}
          <div
            style={{
              borderTop: "1px solid var(--border-subtle)",
              paddingTop: "var(--space-6)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "var(--space-4)",
            }}
          >
            <div>
              {challenge.xp_awarded > 0 ? (
                <div style={{ color: "var(--status-success)", fontWeight: 700, display: "flex", alignItems: "center", gap: "6px" }}>
                  <span>✓</span> Claimed (+{challenge.xp_awarded} XP)
                </div>
              ) : challenge.solved ? (
                <div style={{ color: "var(--status-success)", fontWeight: 600 }}>
                  Problem Solved! Ready to claim reward.
                </div>
              ) : (
                <div style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
                  Solve the problem in the code editor to unlock XP.
                </div>
              )}
            </div>

            <div style={{ display: "flex", gap: "var(--space-3)" }}>
              <button
                onClick={() => onNavigate(`/problems/${challenge.problem_id}`)}
                style={{
                  backgroundColor: "var(--bg-tertiary)",
                  color: "var(--text-primary)",
                  border: "1px solid var(--border-muted)",
                  padding: "10px 20px",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  fontWeight: 600,
                }}
              >
                Go to Workspace ↗
              </button>

              {challenge.can_claim && (
                <button
                  disabled={claiming}
                  onClick={handleClaim}
                  style={{
                    backgroundColor: "var(--status-success)",
                    color: "#ffffff",
                    border: "none",
                    padding: "10px 24px",
                    borderRadius: "var(--radius-md)",
                    cursor: "pointer",
                    fontWeight: 700,
                    boxShadow: "0 4px 14px rgba(16, 185, 129, 0.3)",
                  }}
                >
                  {claiming ? "Claiming..." : "Claim Daily Reward 🎉"}
                </button>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {/* Rules Notice */}
      <div
        style={{
          marginTop: "var(--space-8)",
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-md)",
          padding: "var(--space-4)",
          fontSize: "0.8125rem",
          color: "var(--text-muted)",
          lineHeight: 1.5,
        }}
      >
        <strong style={{ color: "var(--text-primary)" }}>Rules & Idempotency:</strong> Daily challenges are
        deterministic per UTC day. Solves completed within the day earn the base XP reward. Solving on the very first
        submission awards an additional +25 XP bonus. Daily rewards can only be claimed once per calendar day.
      </div>
    </div>
  );
};
