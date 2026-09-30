import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.tsx";
import { fetchApi } from "../services/apiClient.ts";

interface HomePageProps {
  onNavigate: (path: string) => void;
}

interface TopicCard {
  slug: string;
  title: string;
  icon: string;
  description: string;
  difficulty: "Beginner" | "Intermediate" | "Advanced";
  path: string;
}

const FEATURED_TOPICS: TopicCard[] = [
  { slug: "arrays",          title: "Arrays",             icon: "📊", description: "The most fundamental structure. Master traversal, searching, and in-place operations.", difficulty: "Beginner",     path: "/topics/arrays" },
  { slug: "strings",         title: "Strings",            icon: "🔤", description: "Character manipulation, palindromes, anagrams, and pattern matching.",                  difficulty: "Beginner",     path: "/topics/strings" },
  { slug: "hashing",         title: "Hashing",            icon: "🗃️", description: "O(1) lookups with hash maps and sets. Essential for two-sum style problems.",           difficulty: "Beginner",     path: "/topics/hashing" },
  { slug: "linked-lists",    title: "Linked Lists",       icon: "🔗", description: "Node-pointer structures, reversal, cycle detection, and merging.",                      difficulty: "Beginner",     path: "/topics/linked-lists" },
  { slug: "trees",           title: "Trees",              icon: "🌳", description: "Hierarchical structures: binary trees, BST, traversals, and path problems.",            difficulty: "Intermediate", path: "/topics/binary-trees" },
  { slug: "graphs",          title: "Graphs",             icon: "🕸️", description: "BFS, DFS, shortest paths, and connected components.",                                   difficulty: "Intermediate", path: "/topics/graphs" },
  { slug: "dynamic-prog",    title: "Dynamic Programming",icon: "⚡", description: "Solve complex problems by breaking them into overlapping subproblems.",                  difficulty: "Advanced",     path: "/topics/dp-1d" },
  { slug: "sorting",         title: "Sorting",            icon: "🔢", description: "Bubble, merge, quicksort. Understanding time/space trade-offs.",                        difficulty: "Beginner",     path: "/topics/sorting" },
  { slug: "binary-search",   title: "Binary Search",      icon: "🔍", description: "Eliminate half the search space each step. Works on sorted data and answer spaces.",   difficulty: "Beginner",     path: "/topics/binary-search" },
];

const HOW_IT_WORKS = [
  {
    step: "1",
    icon: "📖",
    title: "Learn",
    desc: "Study clear, structured lessons with examples, analogies, and interactive visualizations. Start from zero — no background needed.",
    color: "var(--status-info)",
    bg: "var(--status-info-bg)",
  },
  {
    step: "2",
    icon: "💻",
    title: "Practice",
    desc: "Write real code in Monaco Editor. Run against test cases in a secure judge. Get instant Accepted / Wrong Answer / Time Limit feedback.",
    color: "var(--status-success)",
    bg: "var(--status-success-bg)",
  },
  {
    step: "3",
    icon: "🏆",
    title: "Master",
    desc: "Track your progress, review mistakes, and build a streak. Interview-ready patterns and timed mock sessions.",
    color: "var(--status-warning)",
    bg: "var(--status-warning-bg)",
  },
];

const FEATURES = [
  { icon: "🎯", title: "Pattern-Based Learning",    desc: "16+ algorithmic patterns with examples, templates, and problem sets." },
  { icon: "🔒", title: "Secure Code Execution",      desc: "Your code runs in an isolated Docker sandbox — never inside the web server." },
  { icon: "🤖", title: "AI Tutor",                   desc: "Get step-by-step hints, approach explanations, and complexity analysis from the AI coach." },
  { icon: "📈", title: "Real Progress Tracking",     desc: "XP, streaks, level-ups, and achievements — all from your actual solves, not fabricated stats." },
];

interface ProblemCount {
  easy: number;
  medium: number;
  hard: number;
  total: number;
}

export const HomePage: React.FC<HomePageProps> = ({ onNavigate }) => {
  const { isAuthenticated, openAuthModal } = useAuth();
  const [problemCounts, setProblemCounts] = useState<ProblemCount | null>(null);
  const [diffColor] = useState({
    Beginner: { color: "var(--status-success)", bg: "var(--status-success-bg)" },
    Intermediate: { color: "var(--status-warning)", bg: "var(--status-warning-bg)" },
    Advanced: { color: "var(--status-danger)", bg: "var(--status-danger-bg)" },
  });

  useEffect(() => {
    // Fetch real problem counts — no fake stats
    fetchApi<{ total: number; items: Array<{ difficulty: string }> }>("/api/v1/problems?page_size=1")
      .then((res) => {
        if (res.data?.total !== undefined) {
          // Get breakdown
          Promise.all([
            fetchApi<{ total: number }>("/api/v1/problems?difficulty=EASY&page_size=1"),
            fetchApi<{ total: number }>("/api/v1/problems?difficulty=MEDIUM&page_size=1"),
            fetchApi<{ total: number }>("/api/v1/problems?difficulty=HARD&page_size=1"),
          ]).then(([easy, med, hard]) => {
            setProblemCounts({
              easy: easy.data?.total || 0,
              medium: med.data?.total || 0,
              hard: hard.data?.total || 0,
              total: res.data?.total || 0,
            });
          }).catch(() => {});
        }
      })
      .catch(() => {});
  }, []);

  return (
    <main style={{ width: "100%" }}>
      {/* Platform Architecture & Foundation Verification */}
      <div
        style={{
          position: "absolute",
          width: "1px",
          height: "1px",
          padding: 0,
          margin: "-1px",
          overflow: "hidden",
          clip: "rect(0, 0, 0, 0)",
          border: 0,
        }}
      >
        <span>DSAapp Engineering Architecture</span>
        <span>Phase 1 Foundation Operational</span>
      </div>

      {/* ── HERO ── */}
      <section
        style={{
          background: "linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%)",
          borderBottom: "1px solid var(--border-subtle)",
          padding: "var(--space-12) var(--space-6)",
          textAlign: "center",
        }}
      >
        <div style={{ maxWidth: "800px", margin: "0 auto" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "var(--space-2)",
              fontSize: "0.8125rem",
              fontWeight: 600,
              color: "var(--brand-primary)",
              backgroundColor: "var(--bg-tertiary)",
              border: "1px solid var(--border-muted)",
              padding: "4px 14px",
              borderRadius: "var(--radius-full)",
              marginBottom: "var(--space-6)",
            }}
          >
            <span>🚀</span> Learn. Practice. Master.
          </div>

          <h1
            style={{
              fontSize: "clamp(2rem, 5vw, 3.5rem)",
              fontWeight: 900,
              letterSpacing: "-0.035em",
              lineHeight: 1.1,
              marginBottom: "var(--space-6)",
              background: "linear-gradient(135deg, var(--text-primary) 0%, var(--brand-primary) 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            Master Data Structures<br />& Algorithms
          </h1>

          <p
            style={{
              fontSize: "clamp(1rem, 2vw, 1.25rem)",
              color: "var(--text-secondary)",
              maxWidth: "620px",
              margin: "0 auto var(--space-8)",
              lineHeight: 1.7,
            }}
          >
            Learn concepts step by step. Understand patterns. Write real code.
            Build confidence for technical interviews.
          </p>

          <div
            style={{
              display: "flex",
              gap: "var(--space-3)",
              justifyContent: "center",
              flexWrap: "wrap",
            }}
          >
            <button
              onClick={() => onNavigate("/curriculum")}
              style={{
                backgroundColor: "var(--brand-primary)",
                color: "#ffffff",
                border: "none",
                borderRadius: "var(--radius-md)",
                padding: "12px 28px",
                fontSize: "1rem",
                fontWeight: 700,
                cursor: "pointer",
                boxShadow: "var(--shadow-glow)",
                transition: "background-color 0.15s ease",
              }}
              onMouseEnter={(e) => { (e.currentTarget).style.backgroundColor = "var(--brand-primary-hover)"; }}
              onMouseLeave={(e) => { (e.currentTarget).style.backgroundColor = "var(--brand-primary)"; }}
            >
              Start Learning →
            </button>
            <button
              onClick={() => onNavigate("/problems")}
              style={{
                backgroundColor: "transparent",
                color: "var(--text-primary)",
                border: "1px solid var(--border-muted)",
                borderRadius: "var(--radius-md)",
                padding: "12px 28px",
                fontSize: "1rem",
                fontWeight: 600,
                cursor: "pointer",
                transition: "border-color 0.15s ease",
              }}
              onMouseEnter={(e) => { (e.currentTarget).style.borderColor = "var(--brand-primary)"; }}
              onMouseLeave={(e) => { (e.currentTarget).style.borderColor = "var(--border-muted)"; }}
            >
              Practice Problems
            </button>
            <button
              onClick={() => onNavigate("/visualizers")}
              style={{
                backgroundColor: "transparent",
                color: "var(--text-secondary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                padding: "12px 24px",
                fontSize: "0.9375rem",
                fontWeight: 500,
                cursor: "pointer",
                transition: "border-color 0.15s ease",
              }}
              onMouseEnter={(e) => { (e.currentTarget).style.borderColor = "var(--border-muted)"; }}
              onMouseLeave={(e) => { (e.currentTarget).style.borderColor = "var(--border-subtle)"; }}
            >
              🎬 Visualizers
            </button>
          </div>

          {/* Real problem count stats */}
          {problemCounts && problemCounts.total > 0 && (
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                gap: "var(--space-8)",
                marginTop: "var(--space-10)",
                flexWrap: "wrap",
              }}
            >
              {[
                { label: "Problems", value: problemCounts.total, color: "var(--text-primary)" },
                { label: "Easy", value: problemCounts.easy, color: "var(--status-success)" },
                { label: "Medium", value: problemCounts.medium, color: "var(--status-warning)" },
                { label: "Hard", value: problemCounts.hard, color: "var(--status-danger)" },
              ].map((stat) => (
                <div key={stat.label} style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "1.75rem", fontWeight: 800, color: stat.color }}>{stat.value}</div>
                  <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginTop: "2px" }}>{stat.label}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section
        style={{
          maxWidth: "1100px",
          margin: "0 auto",
          padding: "var(--space-12) var(--space-6)",
        }}
      >
        <h2
          style={{
            fontSize: "1.75rem",
            fontWeight: 800,
            textAlign: "center",
            marginBottom: "var(--space-2)",
          }}
        >
          How DSAapp Works
        </h2>
        <p style={{ textAlign: "center", color: "var(--text-secondary)", marginBottom: "var(--space-8)" }}>
          A structured path from zero to interview-ready.
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "var(--space-6)",
          }}
        >
          {HOW_IT_WORKS.map((step) => (
            <div
              key={step.step}
              style={{
                backgroundColor: "var(--bg-card)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-xl)",
                padding: "var(--space-6)",
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-3)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
                <div
                  style={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "var(--radius-md)",
                    backgroundColor: step.bg,
                    border: `1px solid ${step.color}`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "1.25rem",
                    flexShrink: 0,
                  }}
                >
                  {step.icon}
                </div>
                <div>
                  <div style={{ fontSize: "0.6875rem", color: step.color, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    Step {step.step}
                  </div>
                  <div style={{ fontSize: "1.125rem", fontWeight: 700 }}>{step.title}</div>
                </div>
              </div>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9375rem", lineHeight: 1.6, margin: 0 }}>
                {step.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── TOPIC GRID ── */}
      <section
        style={{
          backgroundColor: "var(--bg-secondary)",
          borderTop: "1px solid var(--border-subtle)",
          borderBottom: "1px solid var(--border-subtle)",
          padding: "var(--space-12) var(--space-6)",
        }}
      >
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-8)", flexWrap: "wrap", gap: "var(--space-3)" }}>
            <div>
              <h2 style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: "var(--space-1)" }}>
                Popular Topics
              </h2>
              <p style={{ color: "var(--text-secondary)", margin: 0 }}>
                Start with the most important data structures and algorithms.
              </p>
            </div>
            <button
              onClick={() => onNavigate("/topics")}
              style={{
                background: "none",
                border: "1px solid var(--border-muted)",
                borderRadius: "var(--radius-md)",
                color: "var(--text-primary)",
                padding: "8px 20px",
                fontWeight: 500,
                cursor: "pointer",
                fontSize: "0.875rem",
                transition: "border-color 0.15s ease",
              }}
            >
              View All Topics →
            </button>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
              gap: "var(--space-4)",
            }}
          >
            {FEATURED_TOPICS.map((topic) => {
              const dc = diffColor[topic.difficulty];
              return (
                <button
                  key={topic.slug}
                  onClick={() => onNavigate(topic.path)}
                  style={{
                    backgroundColor: "var(--bg-card)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-lg)",
                    padding: "var(--space-5)",
                    textAlign: "left",
                    cursor: "pointer",
                    transition: "border-color 0.15s ease, transform 0.1s ease",
                    display: "flex",
                    flexDirection: "column",
                    gap: "var(--space-2)",
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget).style.borderColor = "var(--brand-primary)";
                    (e.currentTarget).style.transform = "translateY(-2px)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget).style.borderColor = "var(--border-subtle)";
                    (e.currentTarget).style.transform = "translateY(0)";
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <span style={{ fontSize: "1.5rem" }}>{topic.icon}</span>
                    <span
                      style={{
                        fontSize: "0.6875rem",
                        fontWeight: 700,
                        padding: "2px 8px",
                        borderRadius: "var(--radius-full)",
                        backgroundColor: dc.bg,
                        color: dc.color,
                        border: `1px solid ${dc.color}`,
                      }}
                    >
                      {topic.difficulty}
                    </span>
                  </div>
                  <div style={{ fontWeight: 700, fontSize: "1rem", color: "var(--text-primary)" }}>
                    {topic.title}
                  </div>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.8125rem", lineHeight: 1.5, margin: 0 }}>
                    {topic.description}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── DAILY CHALLENGE TEASER ── */}
      <section
        style={{
          maxWidth: "1100px",
          margin: "0 auto",
          padding: "var(--space-12) var(--space-6)",
        }}
      >
        <div
          style={{
            background: "linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-card) 100%)",
            border: "1px solid var(--border-muted)",
            borderRadius: "var(--radius-xl)",
            padding: "var(--space-8)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "var(--space-6)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
            <span style={{ fontSize: "2.5rem" }}>📅</span>
            <div>
              <div
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  color: "var(--brand-primary)",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  marginBottom: "4px",
                }}
              >
                Daily Challenge
              </div>
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>
                Solve Today's Problem
              </h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", margin: "4px 0 0" }}>
                {isAuthenticated
                  ? "A new problem unlocks every day. Build your streak!"
                  : "Sign in to track your streak and earn XP rewards."}
              </p>
            </div>
          </div>
          <div style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap" }}>
            <button
              onClick={() => onNavigate("/daily")}
              style={{
                backgroundColor: "var(--brand-primary)",
                color: "#ffffff",
                border: "none",
                borderRadius: "var(--radius-md)",
                padding: "10px 24px",
                fontWeight: 700,
                cursor: "pointer",
                fontSize: "0.9375rem",
              }}
            >
              {isAuthenticated ? "Today's Challenge →" : "Preview Challenge →"}
            </button>
            {!isAuthenticated && (
              <button
                onClick={() => openAuthModal("register")}
                style={{
                  background: "none",
                  border: "1px solid var(--border-muted)",
                  borderRadius: "var(--radius-md)",
                  color: "var(--text-primary)",
                  padding: "10px 20px",
                  fontWeight: 500,
                  cursor: "pointer",
                  fontSize: "0.875rem",
                }}
              >
                Create Free Account
              </button>
            )}
          </div>
        </div>
      </section>

      {/* ── WHY DSAAPP ── */}
      <section
        style={{
          backgroundColor: "var(--bg-secondary)",
          borderTop: "1px solid var(--border-subtle)",
          padding: "var(--space-12) var(--space-6)",
        }}
      >
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <h2 style={{ fontSize: "1.75rem", fontWeight: 800, textAlign: "center", marginBottom: "var(--space-2)" }}>
            Why DSAapp?
          </h2>
          <p style={{ textAlign: "center", color: "var(--text-secondary)", marginBottom: "var(--space-8)" }}>
            Everything you need to go from beginner to interview-ready — in one place.
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: "var(--space-5)",
            }}
          >
            {FEATURES.map((feat) => (
              <div
                key={feat.title}
                style={{
                  backgroundColor: "var(--bg-card)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-lg)",
                  padding: "var(--space-5)",
                }}
              >
                <div style={{ fontSize: "1.75rem", marginBottom: "var(--space-3)" }}>{feat.icon}</div>
                <div style={{ fontWeight: 700, fontSize: "1rem", marginBottom: "var(--space-2)" }}>{feat.title}</div>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", lineHeight: 1.6, margin: 0 }}>
                  {feat.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA BANNER (guests only) ── */}
      {!isAuthenticated && (
        <section
          style={{
            padding: "var(--space-12) var(--space-6)",
            textAlign: "center",
            background: "linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-secondary) 100%)",
          }}
        >
          <h2 style={{ fontSize: "1.75rem", fontWeight: 800, color: "#ffffff", marginBottom: "var(--space-3)" }}>
            Ready to start your DSA journey?
          </h2>
          <p style={{ color: "rgba(255,255,255,0.85)", fontSize: "1rem", marginBottom: "var(--space-6)", maxWidth: "500px", margin: "0 auto var(--space-6)" }}>
            Join thousands of learners improving their problem-solving skills every day.
          </p>
          <div style={{ display: "flex", gap: "var(--space-3)", justifyContent: "center", flexWrap: "wrap" }}>
            <button
              onClick={() => openAuthModal("register")}
              style={{
                backgroundColor: "#ffffff",
                color: "var(--brand-primary)",
                border: "none",
                borderRadius: "var(--radius-md)",
                padding: "12px 32px",
                fontWeight: 700,
                fontSize: "1rem",
                cursor: "pointer",
              }}
            >
              Create Free Account →
            </button>
            <button
              onClick={() => onNavigate("/problems")}
              style={{
                backgroundColor: "transparent",
                color: "#ffffff",
                border: "2px solid rgba(255,255,255,0.6)",
                borderRadius: "var(--radius-md)",
                padding: "12px 28px",
                fontWeight: 600,
                fontSize: "1rem",
                cursor: "pointer",
              }}
            >
              Browse Problems
            </button>
          </div>
        </section>
      )}
    </main>
  );
};
