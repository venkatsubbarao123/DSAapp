import React, { useEffect, useState, useCallback } from "react";
import { fetchApi } from "../services/apiClient.ts";
import { useAuth } from "../context/AuthContext.tsx";
import { RevisionItem, ReviewOutcome, RevisionSchedule } from "../types/progress.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";

interface RevisionPageProps {
  onNavigate: (path: string) => void;
}

export const RevisionPage: React.FC<RevisionPageProps> = ({ onNavigate }) => {
  const { isAuthenticated, openAuthModal } = useAuth();
  const [queueItems, setQueueItems] = useState<RevisionItem[]>([]);
  const [dueCount, setDueCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Review status notification
  const [lastReviewFeedback, setLastReviewFeedback] = useState<string | null>(null);
  const [reviewingId, setReviewingId] = useState<string | null>(null);

  // Manual Add Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newSourceType, setNewSourceType] = useState<"LESSON" | "PROBLEM" | "MISTAKE">("PROBLEM");
  const [newSourceId, setNewSourceId] = useState("");
  const [addSubmitting, setAddSubmitting] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const loadQueue = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetchApi<{
        items: RevisionItem[];
        due_items_count: number;
        total_active_items: number;
      }>("/api/v1/revision/queue");

      setQueueItems(res.data.items || []);
      setDueCount(res.data.due_items_count || 0);
      setTotalCount(res.data.total_active_items || 0);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load revision queue.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  const handleReview = async (itemId: string, outcome: ReviewOutcome, title: string) => {
    setReviewingId(itemId);
    try {
      const res = await fetchApi<RevisionSchedule>(`/api/v1/revision/items/${itemId}/review`, {
        method: "POST",
        body: JSON.stringify({ outcome }),
      });

      const nextDue = new Date(res.data.due_at).toLocaleDateString();
      setLastReviewFeedback(
        `Reviewed "${title}" as ${outcome}. Next review in ${res.data.interval_days} day(s) on ${nextDue}.`
      );

      // Remove from current due queue or update
      setQueueItems((prev) => prev.filter((item) => item.id !== itemId && item.public_id !== itemId));
      setDueCount((prev) => Math.max(0, prev - 1));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to record review.");
    } finally {
      setReviewingId(null);
    }
  };

  const handleCreateItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newSourceId.trim()) {
      setAddError("Title and Source identifier are required.");
      return;
    }

    setAddSubmitting(true);
    setAddError(null);

    try {
      await fetchApi<RevisionItem>("/api/v1/revision/items", {
        method: "POST",
        body: JSON.stringify({
          source_type: newSourceType,
          source_id: newSourceId.trim(),
          title: newTitle.trim(),
        }),
      });

      setShowAddModal(false);
      setNewTitle("");
      setNewSourceId("");
      loadQueue();
    } catch (err: unknown) {
      setAddError(err instanceof Error ? err.message : "Failed to add revision item.");
    } finally {
      setAddSubmitting(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <main id="main-content" style={{ flex: 1, maxWidth: "800px", margin: "var(--space-12) auto", padding: "0 var(--space-6)", textAlign: "center" }}>
        <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-xl)", padding: "var(--space-10) var(--space-8)" }}>
          <div style={{ fontSize: "3rem", marginBottom: "var(--space-4)" }}>🔄</div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: "var(--space-3)" }}>
            Spaced Revision Queue
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "1rem", lineHeight: 1.6, maxWidth: "520px", margin: "0 auto var(--space-6) auto" }}>
            Sign in to use algorithmic spaced repetition (SuperMemo SM-2 inspired) for retaining algorithm patterns, data structure tricks, and tricky lessons.
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
            }}
          >
            Sign In to Access Queue
          </button>
        </div>
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
      {/* Header and Add Button */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "var(--space-4)", marginBottom: "var(--space-8)" }}>
        <div>
          <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: "0 0 var(--space-2) 0", letterSpacing: "-0.025em" }}>
            Spaced Revision Queue
          </h1>
          <p style={{ color: "var(--text-secondary)", margin: 0, fontSize: "0.9375rem" }}>
            Algorithmic recall scheduling based on proven memory retention curves.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          style={{
            backgroundColor: "var(--bg-tertiary)",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-primary)",
            padding: "var(--space-2) var(--space-4)",
            borderRadius: "var(--radius-md)",
            fontWeight: 600,
            cursor: "pointer",
            fontSize: "0.875rem",
          }}
        >
          + Add Custom Item
        </button>
      </div>

      {/* Queue Stats Banner */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "var(--space-4)",
          marginBottom: "var(--space-6)",
        }}
      >
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-4) var(--space-5)",
          }}
        >
          <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>Items Due Today</span>
          <div style={{ fontSize: "1.75rem", fontWeight: 800, color: dueCount > 0 ? "var(--status-warning)" : "var(--status-success)" }}>
            {dueCount}
          </div>
        </div>

        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-4) var(--space-5)",
          }}
        >
          <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>Total Tracked in Memory</span>
          <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--text-primary)" }}>
            {totalCount}
          </div>
        </div>
      </div>

      {/* Review Feedback Banner */}
      {lastReviewFeedback && (
        <div
          style={{
            backgroundColor: "var(--status-success-bg)",
            border: "1px solid var(--status-success)",
            color: "var(--status-success)",
            padding: "var(--space-3) var(--space-5)",
            borderRadius: "var(--radius-md)",
            marginBottom: "var(--space-6)",
            fontSize: "0.875rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>✓ {lastReviewFeedback}</span>
          <button
            onClick={() => setLastReviewFeedback(null)}
            style={{ background: "none", border: "none", color: "currentColor", cursor: "pointer", fontSize: "1rem" }}
          >
            ✕
          </button>
        </div>
      )}

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

      {/* Queue Cards */}
      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "var(--space-12) 0" }}>
          <LoadingSpinner size="lg" />
        </div>
      ) : queueItems.length === 0 ? (
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-xl)",
            padding: "var(--space-12) var(--space-6)",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "2.5rem", marginBottom: "var(--space-3)" }}>🎉</div>
          <h3 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 var(--space-2) 0" }}>
            You are all caught up!
          </h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", maxWidth: "480px", margin: "0 auto var(--space-6) auto" }}>
            No problems or lessons are currently due for spaced review. New items will automatically enter your queue as their intervals mature.
          </p>
          <button
            onClick={() => onNavigate("/problems")}
            style={{
              backgroundColor: "var(--brand-primary)",
              color: "#ffffff",
              border: "none",
              padding: "var(--space-2) var(--space-6)",
              borderRadius: "var(--radius-md)",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Practice New Problems →
          </button>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          {queueItems.map((item) => (
            <div
              key={item.id}
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-lg)",
                padding: "var(--space-5) var(--space-6)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "var(--space-4)", marginBottom: "var(--space-3)" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-1)" }}>
                    <span
                      style={{
                        fontSize: "0.6875rem",
                        fontWeight: 700,
                        padding: "2px 8px",
                        borderRadius: "var(--radius-sm)",
                        backgroundColor: "var(--bg-tertiary)",
                        color: "var(--brand-primary)",
                        border: "1px solid var(--border-subtle)",
                      }}
                    >
                      {item.source_type}
                    </span>
                    {item.is_overdue && (
                      <span
                        style={{
                          fontSize: "0.6875rem",
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: "var(--radius-sm)",
                          backgroundColor: "var(--status-danger-bg)",
                          color: "var(--status-danger)",
                          border: "1px solid var(--status-danger)",
                        }}
                      >
                        OVERDUE
                      </span>
                    )}
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      Reviews: {item.schedule?.review_count ?? 0} • Interval: {item.schedule?.interval_days ?? 1}d
                    </span>
                  </div>
                  <h2 style={{ fontSize: "1.125rem", fontWeight: 700, margin: 0 }}>
                    {item.title}
                  </h2>
                </div>
              </div>

              {/* Review Grading Actions */}
              <div
                style={{
                  borderTop: "1px solid var(--border-subtle)",
                  paddingTop: "var(--space-4)",
                  marginTop: "var(--space-3)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  flexWrap: "wrap",
                  gap: "var(--space-3)",
                }}
              >
                <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)", fontWeight: 500 }}>
                  Recall Quality:
                </span>
                <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
                  <button
                    disabled={reviewingId === item.id}
                    onClick={() => handleReview(item.id, "AGAIN", item.title)}
                    style={{
                      backgroundColor: "rgba(239, 68, 68, 0.1)",
                      border: "1px solid var(--status-danger)",
                      color: "var(--status-danger)",
                      padding: "6px 12px",
                      borderRadius: "var(--radius-md)",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    Again (1d)
                  </button>
                  <button
                    disabled={reviewingId === item.id}
                    onClick={() => handleReview(item.id, "HARD", item.title)}
                    style={{
                      backgroundColor: "rgba(234, 179, 8, 0.1)",
                      border: "1px solid var(--status-warning)",
                      color: "var(--status-warning)",
                      padding: "6px 12px",
                      borderRadius: "var(--radius-md)",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    Hard (+20%)
                  </button>
                  <button
                    disabled={reviewingId === item.id}
                    onClick={() => handleReview(item.id, "GOOD", item.title)}
                    style={{
                      backgroundColor: "rgba(59, 130, 246, 0.1)",
                      border: "1px solid var(--brand-primary)",
                      color: "var(--brand-primary)",
                      padding: "6px 12px",
                      borderRadius: "var(--radius-md)",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    Good (+50%)
                  </button>
                  <button
                    disabled={reviewingId === item.id}
                    onClick={() => handleReview(item.id, "EASY", item.title)}
                    style={{
                      backgroundColor: "rgba(16, 185, 129, 0.1)",
                      border: "1px solid var(--status-success)",
                      color: "var(--status-success)",
                      padding: "6px 12px",
                      borderRadius: "var(--radius-md)",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    Easy (2x)
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Item Modal */}
      {showAddModal && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="add-modal-title"
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 100,
            padding: "var(--space-4)",
          }}
        >
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-xl)",
              maxWidth: "500px",
              width: "100%",
              padding: "var(--space-6)",
              boxSizing: "border-box",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
              <h2 id="add-modal-title" style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>
                Schedule Custom Revision Item
              </h2>
              <button
                onClick={() => setShowAddModal(false)}
                style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: "1.25rem", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            {addError && (
              <div
                role="alert"
                style={{
                  backgroundColor: "var(--status-danger-bg)",
                  color: "var(--status-danger)",
                  border: "1px solid var(--status-danger)",
                  padding: "var(--space-3)",
                  borderRadius: "var(--radius-md)",
                  marginBottom: "var(--space-4)",
                  fontSize: "0.8125rem",
                }}
              >
                {addError}
              </div>
            )}

            <form onSubmit={handleCreateItem}>
              <div style={{ marginBottom: "var(--space-4)" }}>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, marginBottom: "4px" }}>
                  Item Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Reverse Linked List II In-place"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "var(--space-2) var(--space-3)",
                    backgroundColor: "var(--bg-primary)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    color: "var(--text-primary)",
                    fontSize: "0.875rem",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ marginBottom: "var(--space-4)" }}>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, marginBottom: "4px" }}>
                  Source Type *
                </label>
                <select
                  value={newSourceType}
                  onChange={(e) => setNewSourceType(e.target.value as "LESSON" | "PROBLEM" | "MISTAKE")}
                  style={{
                    width: "100%",
                    padding: "var(--space-2) var(--space-3)",
                    backgroundColor: "var(--bg-primary)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    color: "var(--text-primary)",
                    fontSize: "0.875rem",
                    boxSizing: "border-box",
                  }}
                >
                  <option value="PROBLEM">Problem</option>
                  <option value="LESSON">Lesson</option>
                  <option value="MISTAKE">Mistake</option>
                </select>
              </div>

              <div style={{ marginBottom: "var(--space-6)" }}>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, marginBottom: "4px" }}>
                  Source Identifier / Slug *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. reverse-linked-list or custom-id"
                  value={newSourceId}
                  onChange={(e) => setNewSourceId(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "var(--space-2) var(--space-3)",
                    backgroundColor: "var(--bg-primary)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    color: "var(--text-primary)",
                    fontSize: "0.875rem",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "var(--space-3)" }}>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  style={{
                    background: "none",
                    border: "1px solid var(--border-subtle)",
                    color: "var(--text-secondary)",
                    padding: "var(--space-2) var(--space-4)",
                    borderRadius: "var(--radius-md)",
                    cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addSubmitting}
                  style={{
                    backgroundColor: "var(--brand-primary)",
                    color: "#ffffff",
                    border: "none",
                    padding: "var(--space-2) var(--space-5)",
                    borderRadius: "var(--radius-md)",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {addSubmitting ? "Scheduling..." : "Schedule Item"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
};
