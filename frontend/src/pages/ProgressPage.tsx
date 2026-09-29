import React, { useEffect, useState } from "react";
import { fetchApi } from "../services/apiClient.ts";
import { useAuth } from "../context/AuthContext.tsx";
import {
  ProgressOverview,
  TopicProgress,
  MasteryInsights,
} from "../types/progress.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";
import { PremiumGate } from "../components/common/PremiumGate.tsx";

interface ProgressPageProps {
  onNavigate: (path: string) => void;
}

export const ProgressPage: React.FC<ProgressPageProps> = ({ onNavigate }) => {
  const { isAuthenticated, isPremium, openAuthModal } = useAuth();
  const [overview, setOverview] = useState<ProgressOverview | null>(null);
  const [topicProgress, setTopicProgress] = useState<TopicProgress[]>([]);
  const [mastery, setMastery] = useState<MasteryInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    const loadData = async () => {
      try {
        const [ovRes, topRes] = await Promise.all([
          fetchApi<ProgressOverview>("/api/v1/progress/overview"),
          fetchApi<TopicProgress[]>("/api/v1/progress/topics"),
        ]);

        if (!isMounted) return;
        setOverview(ovRes.data);
        setTopicProgress(topRes.data || []);

        if (isPremium) {
          try {
            const mastRes = await fetchApi<MasteryInsights>("/api/v1/progress/insights/mastery");
            if (isMounted) setMastery(mastRes.data);
          } catch {
            // Ignore optional mastery error
          }
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        const msg = err instanceof Error ? err.message : "Failed to load progress data.";
        setError(msg);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadData();

    return () => {
      isMounted = false;
    };
  }, [isAuthenticated, isPremium]);

  if (!isAuthenticated) {
    return (
      <main
        id="main-content"
        style={{
          flex: 1,
          maxWidth: "800px",
          margin: "var(--space-12) auto",
          padding: "0 var(--space-6)",
          textAlign: "center",
        }}
      >
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-xl)",
            padding: "var(--space-10) var(--space-8)",
          }}
        >
          <div style={{ fontSize: "3rem", marginBottom: "var(--space-4)" }}>📊</div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: "var(--space-3)" }}>
            Track Your DSA Learning Journey
          </h1>
          <p
            style={{
              color: "var(--text-secondary)",
              fontSize: "1rem",
              lineHeight: 1.6,
              maxWidth: "520px",
              margin: "0 auto var(--space-6) auto",
            }}
          >
            Sign in to track completed lessons, attempted problems, mistake patterns, and automated spaced revision schedules.
          </p>
          <button
            onClick={() => openAuthModal("login")}
            style={{
              backgroundColor: "var(--brand-primary)",
              color: "#ffffff",
              border: "none",
              padding: "var(--space-3) var(--space-8)",
              borderRadius: "var(--radius-md)",
              fontWeight: 600,
              cursor: "pointer",
              fontSize: "1rem",
            }}
          >
            Sign In to View Progress
          </button>
        </div>
      </main>
    );
  }

  if (loading) {
    return (
      <main id="main-content" style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center" }}>
        <LoadingSpinner size="lg" />
      </main>
    );
  }

  return (
    <main
      id="main-content"
      style={{
        flex: 1,
        maxWidth: "1140px",
        margin: "0 auto",
        padding: "var(--space-8) var(--space-6)",
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      {/* Top Header */}
      <div style={{ marginBottom: "var(--space-8)" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: "0 0 var(--space-2) 0", letterSpacing: "-0.025em" }}>
          Learning Progress & Metrics
        </h1>
        <p style={{ color: "var(--text-secondary)", margin: 0, fontSize: "0.9375rem" }}>
          Mathematical progress tracking computed server-authoritatively across your lessons, problems, and spaced reviews.
        </p>
      </div>

      {error && (
        <div
          role="alert"
          style={{
            backgroundColor: "var(--status-danger-bg)",
            border: "1px solid var(--status-danger)",
            color: "var(--status-danger)",
            padding: "var(--space-4)",
            borderRadius: "var(--radius-md)",
            marginBottom: "var(--space-6)",
          }}
        >
          {error}
        </div>
      )}

      {/* KPI Overview Cards */}
      {overview && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "var(--space-4)",
            marginBottom: "var(--space-8)",
          }}
        >
          {/* Card 1: Overall Completion */}
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-5)",
            }}
          >
            <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)", fontWeight: 600 }}>
              Overall Completion
            </span>
            <div style={{ fontSize: "2rem", fontWeight: 800, margin: "var(--space-2) 0", color: "var(--brand-primary)" }}>
              {overview.overall_completion_percent}%
            </div>
            <div
              style={{
                width: "100%",
                height: "6px",
                backgroundColor: "var(--bg-tertiary)",
                borderRadius: "var(--radius-full)",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${Math.min(overview.overall_completion_percent, 100)}%`,
                  height: "100%",
                  backgroundColor: "var(--brand-primary)",
                  transition: "width 0.3s ease",
                }}
              />
            </div>
          </div>

          {/* Card 2: Lessons Completed */}
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-5)",
            }}
          >
            <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)", fontWeight: 600 }}>
              Lessons Completed
            </span>
            <div style={{ fontSize: "2rem", fontWeight: 800, margin: "var(--space-2) 0", color: "var(--text-primary)" }}>
              {overview.lessons_completed}{" "}
              <span style={{ fontSize: "1rem", color: "var(--text-muted)", fontWeight: 400 }}>
                / {overview.total_visible_lessons}
              </span>
            </div>
            <span style={{ fontSize: "0.75rem", color: "var(--status-success)" }}>
              {overview.lesson_completion_percent}% Completed
            </span>
          </div>

          {/* Card 3: Problems Solved */}
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-5)",
            }}
          >
            <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)", fontWeight: 600 }}>
              Problems Solved
            </span>
            <div style={{ fontSize: "2rem", fontWeight: 800, margin: "var(--space-2) 0", color: "var(--text-primary)" }}>
              {overview.problems_solved}{" "}
              <span style={{ fontSize: "1rem", color: "var(--text-muted)", fontWeight: 400 }}>
                / {overview.total_visible_problems}
              </span>
            </div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              {overview.problems_attempted} Attempted ({overview.problem_solving_percent}% Solved)
            </span>
          </div>

          {/* Card 4: Actionable Queues */}
          <div
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
              <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)", fontWeight: 600 }}>
                Due Revisions & Mistakes
              </span>
              <div style={{ display: "flex", gap: "var(--space-4)", marginTop: "var(--space-2)" }}>
                <div>
                  <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--status-warning)" }}>
                    {overview.due_revisions_count}
                  </div>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Revisions Due</span>
                </div>
                <div>
                  <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--status-danger)" }}>
                    {overview.unresolved_mistakes_count}
                  </div>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Open Mistakes</span>
                </div>
              </div>
            </div>
            <div style={{ display: "flex", gap: "var(--space-2)", marginTop: "var(--space-3)" }}>
              <button
                onClick={() => onNavigate("/revision")}
                style={{
                  background: "var(--bg-tertiary)",
                  border: "1px solid var(--border-subtle)",
                  color: "var(--text-primary)",
                  padding: "4px 8px",
                  borderRadius: "var(--radius-sm)",
                  fontSize: "0.75rem",
                  cursor: "pointer",
                }}
              >
                Review Queue →
              </button>
              <button
                onClick={() => onNavigate("/mistakes")}
                style={{
                  background: "var(--bg-tertiary)",
                  border: "1px solid var(--border-subtle)",
                  color: "var(--text-primary)",
                  padding: "4px 8px",
                  borderRadius: "var(--radius-sm)",
                  fontSize: "0.75rem",
                  cursor: "pointer",
                }}
              >
                Notebook →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Grid: Topic Progress & Activity */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "var(--space-8)", marginBottom: "var(--space-10)" }}>
        {/* Left Column: Topics Breakdown */}
        <section>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "var(--space-4)" }}>
            Topic Mastery & Progress
          </h2>
          {topicProgress.length === 0 ? (
            <div
              style={{
                backgroundColor: "var(--bg-secondary)",
                padding: "var(--space-6)",
                borderRadius: "var(--radius-lg)",
                textAlign: "center",
                color: "var(--text-muted)",
              }}
            >
              No curriculum topics available yet.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
              {topicProgress.map((tp) => (
                <div
                  key={tp.topic_id}
                  style={{
                    backgroundColor: "var(--bg-secondary)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    padding: "var(--space-4)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-2)" }}>
                    <button
                      onClick={() => onNavigate(`/topics/${tp.topic_slug}`)}
                      style={{
                        background: "none",
                        border: "none",
                        padding: 0,
                        color: "var(--text-primary)",
                        fontWeight: 600,
                        fontSize: "0.9375rem",
                        cursor: "pointer",
                        textAlign: "left",
                      }}
                    >
                      {tp.topic_title}
                    </button>
                    <span style={{ fontSize: "0.8125rem", fontWeight: 700, color: "var(--brand-primary)" }}>
                      {tp.completion_percent}%
                    </span>
                  </div>

                  <div
                    style={{
                      width: "100%",
                      height: "6px",
                      backgroundColor: "var(--bg-tertiary)",
                      borderRadius: "var(--radius-full)",
                      overflow: "hidden",
                      marginBottom: "var(--space-2)",
                    }}
                  >
                    <div
                      style={{
                        width: `${Math.min(tp.completion_percent, 100)}%`,
                        height: "100%",
                        backgroundColor: "var(--brand-primary)",
                      }}
                    />
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    <span>
                      Lessons: {tp.completed_lessons} / {tp.total_lessons}
                    </span>
                    <span>
                      Problems: {tp.solved_problems} / {tp.total_problems}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Right Column: Recent Activity */}
        <section>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "var(--space-4)" }}>
            Recent Activity
          </h2>
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-4)",
            }}
          >
            {(!overview?.recent_activity || overview.recent_activity.length === 0) ? (
              <p style={{ margin: 0, fontSize: "0.875rem", color: "var(--text-muted)", textAlign: "center", padding: "var(--space-4) 0" }}>
                No recent activity recorded yet. Start solving problems or reading lessons!
              </p>
            ) : (
              <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
                {overview.recent_activity.map((act, idx) => (
                  <li
                    key={idx}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      borderBottom: idx < overview.recent_activity.length - 1 ? "1px solid var(--border-subtle)" : "none",
                      paddingBottom: "var(--space-2)",
                    }}
                  >
                    <div>
                      <button
                        onClick={() =>
                          onNavigate(act.entity_type === "PROBLEM" ? `/problems/${act.slug}` : `/lessons/${act.slug}`)
                        }
                        style={{
                          background: "none",
                          border: "none",
                          padding: 0,
                          color: "var(--text-primary)",
                          fontSize: "0.8125rem",
                          fontWeight: 600,
                          cursor: "pointer",
                          display: "block",
                          textAlign: "left",
                        }}
                      >
                        {act.title}
                      </button>
                      <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                        {act.entity_type} • {act.status}
                      </span>
                    </div>
                    <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                      {new Date(act.timestamp).toLocaleDateString()}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>

      {/* Pro Mastery Insights Section */}
      <section style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "var(--space-8)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-4)" }}>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>
            Pro Mastery Analytics
          </h2>
          <span
            style={{
              fontSize: "0.6875rem",
              fontWeight: 700,
              padding: "1px 6px",
              borderRadius: "var(--radius-sm)",
              backgroundColor: "rgba(234, 179, 8, 0.2)",
              color: "var(--status-warning)",
              border: "1px solid var(--status-warning)",
            }}
          >
            PRO FEATURE
          </span>
        </div>

        {!isPremium ? (
          <PremiumGate
            contentType="mastery"
            onUpgrade={() => onNavigate("/premium")}
          />
        ) : (
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-6)",
            }}
          >
            {mastery ? (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "var(--space-6)" }}>
                <div>
                  <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>Spaced Retention Score</span>
                  <div style={{ fontSize: "2rem", fontWeight: 800, color: "var(--status-success)", margin: "var(--space-1) 0" }}>
                    {mastery.spaced_retention_score}%
                  </div>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    Calculated from ease factors across reviews
                  </span>
                </div>

                <div>
                  <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>Active Study Streak</span>
                  <div style={{ fontSize: "2rem", fontWeight: 800, color: "var(--brand-primary)", margin: "var(--space-1) 0" }}>
                    {mastery.streak_days} Days
                  </div>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    Continuous consecutive activity
                  </span>
                </div>

                <div>
                  <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>Frequent Mistakes</span>
                  <div style={{ marginTop: "var(--space-2)", display: "flex", flexDirection: "column", gap: "4px" }}>
                    {Object.entries(mastery.mistake_breakdown || {}).length === 0 ? (
                      <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>No mistake trends recorded.</span>
                    ) : (
                      Object.entries(mastery.mistake_breakdown).map(([typ, cnt]) => (
                        <div key={typ} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem" }}>
                          <span>{typ.replace(/_/g, " ")}:</span>
                          <strong>{cnt}</strong>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <div>
                  <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>Pattern Mastery</span>
                  <div style={{ marginTop: "var(--space-2)", display: "flex", flexDirection: "column", gap: "4px" }}>
                    {mastery.pattern_mastery && mastery.pattern_mastery.length > 0 ? (
                      mastery.pattern_mastery.map((pm, idx) => (
                        <div key={idx} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem" }}>
                          <span>{pm.pattern}:</span>
                          <span style={{ color: "var(--status-success)", fontWeight: 600 }}>{pm.level}</span>
                        </div>
                      ))
                    ) : (
                      <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>Solve more pattern problems to unlock.</span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <p style={{ margin: 0, color: "var(--text-muted)" }}>Loading pro analytics...</p>
            )}
          </div>
        )}
      </section>
    </main>
  );
};
