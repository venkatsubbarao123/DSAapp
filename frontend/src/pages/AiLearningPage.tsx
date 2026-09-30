import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.tsx";
import { fetchApi } from "../services/apiClient.ts";
import {
  AIUsageSummaryData,
  ComplexityResponseData,
  ExplainResponseData,
  HintResponseData,
  PatternResponseData,
  RecommendationResponseData,
  TutorResponseData,
} from "../types/ai.ts";

interface AiLearningPageProps {
  onNavigate: (path: string) => void;
}

export const AiLearningPage: React.FC<AiLearningPageProps> = ({ onNavigate }) => {
  const { isAuthenticated, openAuthModal } = useAuth();
  const [activeTab, setActiveTab] = useState<
    "tutor" | "hint" | "explain" | "complexity" | "pattern" | "recommendations"
  >("tutor");

  // Telemetry & Quota
  const [usage, setUsage] = useState<AIUsageSummaryData | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // 1. Tutor State
  const [tutorQuestion, setTutorQuestion] = useState("");
  const [tutorCode, setTutorCode] = useState("");
  const [tutorResponse, setTutorResponse] = useState<TutorResponseData | null>(null);

  // 2. Hint State
  const [hintProblemId, setHintProblemId] = useState("find-maximum-in-array");
  const [currentHintLevel, setCurrentHintLevel] = useState(1);
  const [hintResponse, setHintResponse] = useState<HintResponseData | null>(null);

  // 3. Explain State
  const [explainType, setExplainType] = useState<"concept" | "code" | "judge_error">("code");
  const [explainInput, setExplainInput] = useState("");
  const [explainResponse, setExplainResponse] = useState<ExplainResponseData | null>(null);

  // 4. Complexity State
  const [complexityCode, setComplexityCode] = useState(
    "def binary_search(arr, target):\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1"
  );
  const [complexityResponse, setComplexityResponse] = useState<ComplexityResponseData | null>(null);

  // 5. Pattern State
  const [patternInput, setPatternInput] = useState(
    "Given a 1-indexed array of integers sorted in non-decreasing order, find two numbers that sum up to target."
  );
  const [patternResponse, setPatternResponse] = useState<PatternResponseData | null>(null);

  // 6. Recommendations State
  const [recommendations, setRecommendations] = useState<RecommendationResponseData | null>(null);

  // Fetch usage stats on mount if authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchApi<AIUsageSummaryData>("/api/v1/ai/usage")
        .then((res) => {
          const data = (res as any)?.data ?? res;
          if (data && (data.daily_quota !== undefined || data.daily_used !== undefined)) {
            setUsage(data);
          }
        })
        .catch(() => {});
    }
  }, [isAuthenticated, activeTab]);

  // Load recommendations when opening tab
  useEffect(() => {
    if (isAuthenticated && activeTab === "recommendations" && !recommendations) {
      setLoading(true);
      fetchApi<RecommendationResponseData>("/api/v1/ai/recommendations")
        .then((res) => {
          const data = (res as any)?.data ?? res;
          if (data && data.recommendations) {
            setRecommendations(data);
          }
        })
        .catch((err) => setErrorMsg(err.message))
        .finally(() => setLoading(false));
    }
  }, [isAuthenticated, activeTab, recommendations]);

  if (!isAuthenticated) {
    return (
      <main style={{ maxWidth: "800px", margin: "60px auto", padding: "0 24px", textAlign: "center" }}>
        <div style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: "48px 24px" }}>
          <h1 style={{ fontSize: "1.8rem", color: "var(--text-primary)", marginBottom: "12px" }}>
            DSA AI Learning Assistant
          </h1>
          <p style={{ color: "var(--text-secondary)", marginBottom: "24px" }}>
            Sign in to access AI-powered pedagogical tutoring, progressive hint disclosure, Big-O complexity analysis, and personalized recommendations.
          </p>
          <button
            onClick={() => openAuthModal("login")}
            style={{
              padding: "10px 24px",
              backgroundColor: "var(--brand-primary)",
              color: "#ffffff",
              border: "none",
              borderRadius: "var(--radius-sm)",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            Sign In to Access AI
          </button>
        </div>
      </main>
    );
  }

  const handleAskTutor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tutorQuestion.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetchApi<TutorResponseData>("/api/v1/ai/tutor", {
        method: "POST",
        body: JSON.stringify({
          question: tutorQuestion,
          code_context: tutorCode || undefined,
        }),
      });
      const data = (res as any)?.data ?? res;
      if (data && data.explanation) {
        setTutorResponse(data);
        // Refresh usage telemetry
        fetchApi<AIUsageSummaryData>("/api/v1/ai/usage").then((u) => {
          const uData = (u as any)?.data ?? u;
          if (uData && (uData.daily_quota !== undefined || uData.daily_used !== undefined)) setUsage(uData);
        });
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to contact AI Tutor.");
    } finally {
      setLoading(false);
    }
  };

  const handleFetchHint = async (level: number) => {
    setLoading(true);
    setErrorMsg(null);
    setCurrentHintLevel(level);
    try {
      const res = await fetchApi<HintResponseData>("/api/v1/ai/hint", {
        method: "POST",
        body: JSON.stringify({
          problem_id: hintProblemId,
          hint_level: level,
        }),
      });
      const data = (res as any)?.data ?? res;
      if (data && data.hint_content) {
        setHintResponse(data);
        fetchApi<AIUsageSummaryData>("/api/v1/ai/usage").then((u) => {
          const uData = (u as any)?.data ?? u;
          if (uData && (uData.daily_quota !== undefined || uData.daily_used !== undefined)) setUsage(uData);
        });
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to fetch progressive hint.");
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = async () => {
    if (!explainInput.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetchApi<ExplainResponseData>("/api/v1/ai/explain", {
        method: "POST",
        body: JSON.stringify({
          target_type: explainType,
          context_text: explainInput,
        }),
      });
      const data = (res as any)?.data ?? res;
      if (data && data.explanation) {
        setExplainResponse(data);
        fetchApi<AIUsageSummaryData>("/api/v1/ai/usage").then((u) => {
          const uData = (u as any)?.data ?? u;
          if (uData && (uData.daily_quota !== undefined || uData.daily_used !== undefined)) setUsage(uData);
        });
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to generate explanation.");
    } finally {
      setLoading(false);
    }
  };

  const handleComplexity = async () => {
    if (!complexityCode.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetchApi<ComplexityResponseData>("/api/v1/ai/complexity", {
        method: "POST",
        body: JSON.stringify({ code: complexityCode }),
      });
      const data = (res as any)?.data ?? res;
      if (data && data.time_complexity) {
        setComplexityResponse(data);
        fetchApi<AIUsageSummaryData>("/api/v1/ai/usage").then((u) => {
          const uData = (u as any)?.data ?? u;
          if (uData && (uData.daily_quota !== undefined || uData.daily_used !== undefined)) setUsage(uData);
        });
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to analyze complexity.");
    } finally {
      setLoading(false);
    }
  };

  const handlePattern = async () => {
    if (!patternInput.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetchApi<PatternResponseData>("/api/v1/ai/pattern", {
        method: "POST",
        body: JSON.stringify({ problem_description: patternInput }),
      });
      const data = (res as any)?.data ?? res;
      if (data && data.primary_pattern) {
        setPatternResponse(data);
        fetchApi<AIUsageSummaryData>("/api/v1/ai/usage").then((u) => {
          const uData = (u as any)?.data ?? u;
          if (uData && (uData.daily_quota !== undefined || uData.daily_used !== undefined)) setUsage(uData);
        });
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to detect pattern.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main
      style={{
        maxWidth: "1280px",
        margin: "0 auto",
        padding: "var(--space-8) var(--space-6)",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-6)",
      }}
    >
      {/* Top Header & Quota */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "var(--space-4)" }}>
        <div>
          <h1 style={{ fontSize: "2rem", margin: 0, color: "var(--text-primary)" }}>
            AI Learning Assistant & Tutor
          </h1>
          <p style={{ color: "var(--text-secondary)", margin: "var(--space-1) 0 0 0" }}>
            Pedagogical concept tutoring, tiered progressive hints, Big-O derivation, and pattern recognition.
          </p>
        </div>

        {usage && (
          <div
            style={{
              padding: "8px 16px",
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              display: "flex",
              alignItems: "center",
              gap: "var(--space-3)",
            }}
          >
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Daily Quota:</span>
            <span style={{ fontWeight: 700, color: usage.daily_remaining > 0 ? "var(--status-success)" : "var(--status-danger)" }}>
              {usage.daily_remaining} / {usage.daily_quota} remaining
            </span>
            <span
              style={{
                fontSize: "0.75rem",
                padding: "2px 8px",
                backgroundColor: usage.is_premium ? "var(--status-warning-bg)" : "var(--bg-tertiary)",
                color: usage.is_premium ? "var(--status-warning)" : "var(--text-secondary)",
                borderRadius: "var(--radius-full)",
                border: "1px solid var(--border-muted)",
              }}
            >
              {usage.is_premium ? "PRO TIER" : "FREE TIER"}
            </span>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div
        style={{
          display: "flex",
          borderBottom: "1px solid var(--border-subtle)",
          gap: "var(--space-2)",
          overflowX: "auto",
        }}
      >
        {[
          { id: "tutor", label: "AI Tutor" },
          { id: "hint", label: "Progressive Hints" },
          { id: "explain", label: "Code & Error Explainer" },
          { id: "complexity", label: "Complexity Analyzer" },
          { id: "pattern", label: "Pattern Detector" },
          { id: "recommendations", label: "Recommendations" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id as any);
              setErrorMsg(null);
            }}
            style={{
              padding: "10px 16px",
              background: "none",
              border: "none",
              borderBottom: activeTab === tab.id ? "2px solid var(--brand-primary)" : "2px solid transparent",
              color: activeTab === tab.id ? "var(--text-primary)" : "var(--text-secondary)",
              fontWeight: activeTab === tab.id ? 700 : 500,
              cursor: "pointer",
              fontSize: "0.95rem",
              whiteSpace: "nowrap",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {errorMsg && (
        <div
          style={{
            padding: "var(--space-3) var(--space-4)",
            backgroundColor: "var(--status-danger-bg)",
            color: "var(--status-danger)",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--status-danger)",
          }}
        >
          {errorMsg}
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          TAB 1: AI TUTOR
      ───────────────────────────────────────────────────────────── */}
      {activeTab === "tutor" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-6)" }}>
          <form
            onSubmit={handleAskTutor}
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-4)",
              backgroundColor: "var(--bg-card)",
              padding: "var(--space-6)",
              borderRadius: "var(--radius-lg)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <h2 style={{ fontSize: "1.2rem", margin: 0, color: "var(--text-primary)" }}>Ask the AI Tutor</h2>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "4px" }}>
                Your Question or Inquiry:
              </label>
              <textarea
                value={tutorQuestion}
                onChange={(e) => setTutorQuestion(e.target.value)}
                placeholder="e.g. How does binary search narrow down the search space? Can you explain the pointer movement intuition?"
                rows={4}
                style={{
                  width: "100%",
                  padding: "10px",
                  backgroundColor: "var(--bg-tertiary)",
                  border: "1px solid var(--border-muted)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "0.9rem",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "4px" }}>
                Optional Code Draft Context:
              </label>
              <textarea
                value={tutorCode}
                onChange={(e) => setTutorCode(e.target.value)}
                placeholder="Optional draft code snippet..."
                rows={4}
                style={{
                  width: "100%",
                  padding: "10px",
                  backgroundColor: "var(--bg-tertiary)",
                  border: "1px solid var(--border-muted)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.85rem",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <button
              type="submit"
              disabled={loading || !tutorQuestion.trim()}
              style={{
                padding: "10px 18px",
                backgroundColor: "var(--brand-primary)",
                border: "none",
                borderRadius: "var(--radius-sm)",
                color: "#ffffff",
                fontWeight: 700,
                cursor: loading ? "wait" : "pointer",
                alignSelf: "flex-start",
              }}
            >
              {loading ? "Thinking..." : "Ask Tutor"}
            </button>
          </form>

          {/* Tutor Response Panel */}
          <div
            style={{
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-6)",
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-4)",
            }}
          >
            <h2 style={{ fontSize: "1.2rem", margin: 0, color: "var(--text-primary)" }}>Tutor Guidance</h2>
            {tutorResponse ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
                <div>
                  <span style={{ fontSize: "0.8rem", textTransform: "uppercase", color: "var(--brand-primary)", fontWeight: 700 }}>
                    Core Explanation
                  </span>
                  <p style={{ margin: "4px 0 0 0", color: "var(--text-primary)", lineHeight: 1.6 }}>
                    {tutorResponse.explanation}
                  </p>
                </div>

                <div style={{ padding: "12px", backgroundColor: "var(--bg-tertiary)", borderRadius: "var(--radius-sm)", borderLeft: "3px solid var(--status-info)" }}>
                  <span style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "var(--status-info)", fontWeight: 700 }}>
                    Key Intuition
                  </span>
                  <p style={{ margin: "4px 0 0 0", color: "var(--text-primary)", fontSize: "0.9rem" }}>
                    {tutorResponse.key_idea}
                  </p>
                </div>

                {tutorResponse.visualization_suggestion && (
                  <div
                    style={{
                      padding: "14px",
                      backgroundColor: "var(--brand-glow)",
                      borderRadius: "var(--radius-md)",
                      border: "1px solid var(--brand-primary)",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <div>
                      <span style={{ fontSize: "0.75rem", textTransform: "uppercase", fontWeight: 700, color: "var(--brand-primary)" }}>
                        Interactive Visualizer Suggestion
                      </span>
                      <p style={{ margin: "2px 0 0 0", fontSize: "0.9rem", color: "var(--text-primary)", fontWeight: 600 }}>
                        {tutorResponse.visualization_suggestion.title}
                      </p>
                    </div>
                    <button
                      onClick={() => onNavigate(`/visualizers`)}
                      style={{
                        padding: "6px 12px",
                        backgroundColor: "var(--brand-primary)",
                        color: "#ffffff",
                        border: "none",
                        borderRadius: "var(--radius-sm)",
                        fontWeight: 600,
                        cursor: "pointer",
                        fontSize: "0.85rem",
                      }}
                    >
                      Open Visualizer &rarr;
                    </button>
                  </div>
                )}

                {tutorResponse.next_step && (
                  <div>
                    <span style={{ fontSize: "0.8rem", textTransform: "uppercase", color: "var(--status-success)", fontWeight: 700 }}>
                      Next Challenge Step
                    </span>
                    <p style={{ margin: "4px 0 0 0", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                      {tutorResponse.next_step}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", fontStyle: "italic" }}>
                Ask a DSA question to receive step-by-step conceptual guidance without spoiling complete solutions.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          TAB 2: PROGRESSIVE HINTS
      ───────────────────────────────────────────────────────────── */}
      {activeTab === "hint" && (
        <div
          style={{
            backgroundColor: "var(--bg-card)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-6)",
          }}
        >
          <div>
            <h2 style={{ fontSize: "1.2rem", margin: 0, color: "var(--text-primary)" }}>
              Progressive Problem Hint Disclosure
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", margin: "4px 0 0 0" }}>
              Tiered hints designed to guide reasoning step-by-step from problem understanding to algorithm pseudocode.
            </p>
          </div>

          {/* Problem Identifier Input & Quick Presets */}
          <div style={{ display: "flex", gap: "var(--space-3)", alignItems: "center", flexWrap: "wrap" }}>
            <label htmlFor="hint-problem-select" style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
              Select Problem:
            </label>
            <select
              id="hint-problem-select"
              value={hintProblemId}
              onChange={(e) => {
                setHintProblemId(e.target.value);
                setHintResponse(null);
              }}
              style={{
                padding: "8px 12px",
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-primary)",
                fontSize: "0.85rem",
              }}
            >
              <option value="find-maximum-in-array">Find Maximum in Array (Easy)</option>
              <option value="reverse-an-array">Reverse an Array (Easy)</option>
              <option value="two-number-sum">Two Number Sum (Easy)</option>
              <option value="valid-parentheses">Valid Parentheses (Easy)</option>
              <option value="find-element-in-sorted-array">Binary Search (Easy)</option>
              <option value="three-number-sum">Three Number Sum (Medium)</option>
              <option value="container-with-maximum-area">Container with Maximum Area (Medium)</option>
              <option value="longest-substring-no-repeat">Longest Substring No Repeat (Medium)</option>
              <option value="climbing-stairs">Climbing Stairs (Medium)</option>
              <option value="two-sum-seed">Two Sum Seed (Fundamentals)</option>
            </select>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>or custom slug/ID:</span>
            <input
              id="hint-problem-input"
              type="text"
              value={hintProblemId}
              onChange={(e) => {
                setHintProblemId(e.target.value);
                setHintResponse(null);
              }}
              placeholder="e.g. reverse-an-array"
              style={{
                padding: "6px 12px",
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-primary)",
                fontSize: "0.85rem",
                width: "200px",
              }}
            />
          </div>

          {/* Hint Tier Buttons */}
          <div style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap" }}>
            {[1, 2, 3, 4, 5].map((lvl) => (
              <button
                key={`hint-tier-${lvl}`}
                onClick={() => handleFetchHint(lvl)}
                disabled={loading}
                style={{
                  padding: "8px 16px",
                  borderRadius: "var(--radius-md)",
                  border: currentHintLevel === lvl ? "1px solid var(--border-focus)" : "1px solid var(--border-muted)",
                  backgroundColor: currentHintLevel === lvl ? "var(--brand-primary)" : "var(--bg-tertiary)",
                  color: currentHintLevel === lvl ? "#ffffff" : "var(--text-secondary)",
                  fontWeight: 600,
                  fontSize: "0.85rem",
                  cursor: "pointer",
                }}
              >
                Hint Tier {lvl} {lvl === 5 && "(Detailed)"}
              </button>
            ))}
          </div>

          {/* Hint Response Card */}
          {hintResponse && (
            <div
              style={{
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                padding: "var(--space-6)",
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-4)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3 style={{ margin: 0, fontSize: "1.1rem", color: "var(--text-primary)" }}>
                  Tier {hintResponse.hint_level}: {hintResponse.title}
                </h3>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  {hintResponse.is_last_hint ? "Final Hint Tier" : `Tier ${hintResponse.hint_level} of 5`}
                </span>
              </div>

              <p style={{ margin: 0, color: "var(--text-primary)", lineHeight: 1.6, fontSize: "0.95rem" }}>
                {hintResponse.hint_content}
              </p>

              <div
                style={{
                  padding: "12px",
                  backgroundColor: "var(--bg-card)",
                  borderRadius: "var(--radius-sm)",
                  borderLeft: "3px solid var(--brand-primary)",
                }}
              >
                <span style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "var(--brand-primary)", fontWeight: 700 }}>
                  Reflection Prompt
                </span>
                <p style={{ margin: "4px 0 0 0", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                  {hintResponse.thought_question}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          TAB 3: EXPLAIN CODE & ERRORS
      ───────────────────────────────────────────────────────────── */}
      {activeTab === "explain" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-6)" }}>
          <div
            style={{
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-6)",
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-4)",
            }}
          >
            <h2 style={{ fontSize: "1.2rem", margin: 0, color: "var(--text-primary)" }}>Explain Code or Error</h2>

            <div style={{ display: "flex", gap: "var(--space-2)" }}>
              {(["code", "judge_error", "concept"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setExplainType(t)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "var(--radius-sm)",
                    backgroundColor: explainType === t ? "var(--brand-primary)" : "var(--bg-tertiary)",
                    border: "1px solid var(--border-muted)",
                    color: explainType === t ? "#ffffff" : "var(--text-secondary)",
                    cursor: "pointer",
                    fontSize: "0.8rem",
                    fontWeight: 600,
                  }}
                >
                  {t.replace("_", " ").toUpperCase()}
                </button>
              ))}
            </div>

            <textarea
              value={explainInput}
              onChange={(e) => setExplainInput(e.target.value)}
              placeholder="Paste code snippet, compiler output, or judge error message..."
              rows={8}
              style={{
                width: "100%",
                padding: "10px",
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-muted)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-primary)",
                fontFamily: "var(--font-mono)",
                fontSize: "0.85rem",
                boxSizing: "border-box",
              }}
            />

            <button
              onClick={handleExplain}
              disabled={loading || !explainInput.trim()}
              style={{
                padding: "10px 18px",
                backgroundColor: "var(--brand-primary)",
                border: "none",
                borderRadius: "var(--radius-sm)",
                color: "#ffffff",
                fontWeight: 700,
                cursor: loading ? "wait" : "pointer",
                alignSelf: "flex-start",
              }}
            >
              {loading ? "Analyzing..." : "Explain"}
            </button>
          </div>

          <div
            style={{
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-6)",
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-4)",
            }}
          >
            <h2 style={{ fontSize: "1.2rem", margin: 0, color: "var(--text-primary)" }}>Diagnostic Breakdown</h2>
            {explainResponse ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
                <p style={{ margin: 0, color: "var(--text-primary)", lineHeight: 1.6 }}>
                  {explainResponse.explanation}
                </p>

                <div>
                  <span style={{ fontSize: "0.8rem", textTransform: "uppercase", color: "var(--brand-primary)", fontWeight: 700 }}>
                    Key Points
                  </span>
                  <ul style={{ margin: "4px 0 0 0", paddingLeft: "20px", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                    {explainResponse.breakdown_points.map((pt, i) => (
                      <li key={i} style={{ marginBottom: "4px" }}>{pt}</li>
                    ))}
                  </ul>
                </div>

                {explainResponse.suggested_fix && (
                  <div style={{ padding: "10px", backgroundColor: "var(--status-success-bg)", borderRadius: "var(--radius-sm)", border: "1px solid var(--status-success)" }}>
                    <span style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "var(--status-success)", fontWeight: 700 }}>
                      Suggested Conceptual Fix
                    </span>
                    <p style={{ margin: "2px 0 0 0", color: "var(--text-primary)", fontSize: "0.9rem" }}>
                      {explainResponse.suggested_fix}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", fontStyle: "italic" }}>
                Provide code or an error message to see a step-by-step educational analysis.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          TAB 4: COMPLEXITY ANALYZER
      ───────────────────────────────────────────────────────────── */}
      {activeTab === "complexity" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-6)" }}>
          <div
            style={{
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-6)",
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-4)",
            }}
          >
            <h2 style={{ fontSize: "1.2rem", margin: 0, color: "var(--text-primary)" }}>Big-O Complexity Analyzer</h2>
            <textarea
              value={complexityCode}
              onChange={(e) => setComplexityCode(e.target.value)}
              rows={12}
              style={{
                width: "100%",
                padding: "10px",
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-muted)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-primary)",
                fontFamily: "var(--font-mono)",
                fontSize: "0.85rem",
                boxSizing: "border-box",
              }}
            />
            <button
              onClick={handleComplexity}
              disabled={loading || !complexityCode.trim()}
              style={{
                padding: "10px 18px",
                backgroundColor: "var(--brand-primary)",
                border: "none",
                borderRadius: "var(--radius-sm)",
                color: "#ffffff",
                fontWeight: 700,
                cursor: loading ? "wait" : "pointer",
                alignSelf: "flex-start",
              }}
            >
              {loading ? "Deriving Big-O..." : "Analyze Complexity"}
            </button>
          </div>

          <div
            style={{
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-6)",
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-4)",
            }}
          >
            <h2 style={{ fontSize: "1.2rem", margin: 0, color: "var(--text-primary)" }}>Complexity Derivation</h2>
            {complexityResponse ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
                <div style={{ display: "flex", gap: "var(--space-4)" }}>
                  <div style={{ flex: 1, padding: "12px", backgroundColor: "var(--bg-tertiary)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Time Complexity</span>
                    <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--status-info)" }}>
                      {complexityResponse.time_complexity}
                    </div>
                  </div>
                  <div style={{ flex: 1, padding: "12px", backgroundColor: "var(--bg-tertiary)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Space Complexity</span>
                    <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--status-warning)" }}>
                      {complexityResponse.space_complexity}
                    </div>
                  </div>
                </div>

                <div>
                  <span style={{ fontSize: "0.8rem", textTransform: "uppercase", color: "var(--brand-primary)", fontWeight: 700 }}>
                    Mathematical Derivation
                  </span>
                  <p style={{ margin: "4px 0 0 0", color: "var(--text-primary)", lineHeight: 1.6, fontSize: "0.9rem" }}>
                    {complexityResponse.reasoning}
                  </p>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "4px", fontSize: "0.85rem" }}>
                  <div><strong>Best Case:</strong> <span style={{ color: "var(--text-secondary)" }}>{complexityResponse.best_case}</span></div>
                  <div><strong>Average Case:</strong> <span style={{ color: "var(--text-secondary)" }}>{complexityResponse.average_case}</span></div>
                  <div><strong>Worst Case:</strong> <span style={{ color: "var(--text-secondary)" }}>{complexityResponse.worst_case}</span></div>
                </div>
              </div>
            ) : (
              <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", fontStyle: "italic" }}>
                Submit code to evaluate theoretical Big-O upper bounds with best, average, and worst-case bounds.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          TAB 5: PATTERN DETECTOR
      ───────────────────────────────────────────────────────────── */}
      {activeTab === "pattern" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-6)" }}>
          <div
            style={{
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-6)",
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-4)",
            }}
          >
            <h2 style={{ fontSize: "1.2rem", margin: 0, color: "var(--text-primary)" }}>Algorithmic Pattern Recognition</h2>
            <textarea
              value={patternInput}
              onChange={(e) => setPatternInput(e.target.value)}
              placeholder="Paste problem statement or code snippet..."
              rows={8}
              style={{
                width: "100%",
                padding: "10px",
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-muted)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-primary)",
                fontSize: "0.9rem",
                boxSizing: "border-box",
              }}
            />
            <button
              onClick={handlePattern}
              disabled={loading || !patternInput.trim()}
              style={{
                padding: "10px 18px",
                backgroundColor: "var(--brand-primary)",
                border: "none",
                borderRadius: "var(--radius-sm)",
                color: "#ffffff",
                fontWeight: 700,
                cursor: loading ? "wait" : "pointer",
                alignSelf: "flex-start",
              }}
            >
              {loading ? "Detecting..." : "Detect Pattern"}
            </button>
          </div>

          <div
            style={{
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-6)",
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-4)",
            }}
          >
            <h2 style={{ fontSize: "1.2rem", margin: 0, color: "var(--text-primary)" }}>Detected Patterns</h2>
            {patternResponse ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
                <div style={{ padding: "12px", backgroundColor: "var(--bg-tertiary)", borderRadius: "var(--radius-md)", borderLeft: "4px solid var(--brand-primary)" }}>
                  <span style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "var(--brand-primary)", fontWeight: 700 }}>
                    Primary Pattern
                  </span>
                  <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--text-primary)" }}>
                    {patternResponse.primary_pattern}
                  </div>
                  <span style={{ fontSize: "0.75rem", color: "var(--status-success)" }}>
                    Confidence: {patternResponse.confidence}
                  </span>
                </div>

                <div>
                  <span style={{ fontSize: "0.8rem", textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 700 }}>
                    Evidence Lines
                  </span>
                  <ul style={{ margin: "4px 0 0 0", paddingLeft: "20px", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                    {patternResponse.evidence.map((ev, i) => (
                      <li key={i} style={{ marginBottom: "4px" }}>
                        <strong>{ev.indicator}</strong>: {ev.relevance}
                      </li>
                    ))}
                  </ul>
                </div>

                {patternResponse.alternative_patterns.length > 0 && (
                  <div>
                    <span style={{ fontSize: "0.8rem", textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 700 }}>
                      Alternative Trade-off Patterns
                    </span>
                    <div style={{ display: "flex", gap: "var(--space-2)", marginTop: "4px" }}>
                      {patternResponse.alternative_patterns.map((alt, i) => (
                        <span key={i} style={{ padding: "2px 8px", backgroundColor: "var(--bg-tertiary)", borderRadius: "var(--radius-sm)", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                          {alt}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", fontStyle: "italic" }}>
                Paste a problem statement to classify canonical algorithmic patterns (Two Pointers, Sliding Window, DP, etc.).
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          TAB 6: PERSONALIZED RECOMMENDATIONS
      ───────────────────────────────────────────────────────────── */}
      {activeTab === "recommendations" && (
        <div
          style={{
            backgroundColor: "var(--bg-card)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-6)",
          }}
        >
          <div>
            <h2 style={{ fontSize: "1.2rem", margin: 0, color: "var(--text-primary)" }}>
              Personalized Learning Path
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", margin: "4px 0 0 0" }}>
              Synthesized from your actual Phase 4 submission attempts, mistake notebook patterns, and revision schedule.
            </p>
          </div>

          {recommendations ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
              {/* Insight Banner */}
              <div
                style={{
                  padding: "16px",
                  backgroundColor: "var(--bg-tertiary)",
                  borderRadius: "var(--radius-md)",
                  borderLeft: "4px solid var(--brand-primary)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div>
                  <span style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "var(--brand-primary)", fontWeight: 700 }}>
                    Learning Diagnostic
                  </span>
                  <p style={{ margin: "4px 0 0 0", color: "var(--text-primary)", fontSize: "0.95rem" }}>
                    {recommendations.summary_insight}
                  </p>
                </div>
                <div style={{ textAlign: "right" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Due for Review</span>
                  <span style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--status-warning)" }}>
                    {recommendations.pending_revisions_count} items
                  </span>
                </div>
              </div>

              {/* Weak Topics Section */}
              {recommendations.weak_topics.length > 0 && (
                <div>
                  <h3 style={{ fontSize: "1rem", color: "var(--text-primary)", marginBottom: "8px" }}>
                    Targeted Cognitive Error Focus
                  </h3>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "var(--space-4)" }}>
                    {recommendations.weak_topics.map((wt, i) => (
                      <div
                        key={i}
                        style={{
                          backgroundColor: "var(--bg-secondary)",
                          padding: "14px",
                          borderRadius: "var(--radius-md)",
                          border: "1px solid var(--border-subtle)",
                        }}
                      >
                        <strong style={{ color: "var(--status-danger)", fontSize: "0.9rem" }}>{wt.topic_title}</strong>
                        <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: "4px 0" }}>
                          Recorded Mistakes: {wt.mistake_count}
                        </div>
                        <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                          {wt.suggested_action}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Problems */}
              <div>
                <h3 style={{ fontSize: "1rem", color: "var(--text-primary)", marginBottom: "8px" }}>
                  Recommended Problem Progression
                </h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
                  {recommendations.recommendations.map((rec) => (
                    <div
                      key={rec.problem_id}
                      style={{
                        padding: "14px 18px",
                        backgroundColor: "var(--bg-secondary)",
                        borderRadius: "var(--radius-md)",
                        border: "1px solid var(--border-subtle)",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                    >
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                          <strong style={{ color: "var(--text-primary)", fontSize: "1rem" }}>{rec.problem_title}</strong>
                          <span style={{ fontSize: "0.75rem", padding: "1px 6px", backgroundColor: "var(--bg-tertiary)", borderRadius: "var(--radius-sm)", color: "var(--brand-primary)" }}>
                            {rec.difficulty}
                          </span>
                        </div>
                        <p style={{ margin: "4px 0 0 0", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                          {rec.reason}
                        </p>
                      </div>
                      <button
                        onClick={() => onNavigate(`/problems/${rec.problem_id}`)}
                        style={{
                          padding: "6px 14px",
                          backgroundColor: "var(--brand-primary)",
                          color: "#ffffff",
                          border: "none",
                          borderRadius: "var(--radius-sm)",
                          fontWeight: 600,
                          cursor: "pointer",
                          fontSize: "0.85rem",
                          whiteSpace: "nowrap",
                        }}
                      >
                        Solve Problem &rarr;
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
              {loading ? "Loading personalized recommendations..." : "No recommendations currently available."}
            </div>
          )}
        </div>
      )}
    </main>
  );
};
