import React, { useEffect, useState, useCallback } from "react";
import { fetchApi } from "../services/apiClient.ts";
import { useAuth } from "../context/AuthContext.tsx";
import { Mistake, MistakeType } from "../types/progress.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";

interface MistakesPageProps {
  onNavigate: (path: string) => void;
}

const MISTAKE_TYPES: MistakeType[] = [
  "CONCEPT_GAP",
  "LOGIC_ERROR",
  "EDGE_CASE",
  "COMPLEXITY_ISSUE",
  "SYNTAX_ERROR",
  "IMPLEMENTATION_ERROR",
  "MISUNDERSTANDING",
  "OTHER",
];

export const MistakesPage: React.FC<MistakesPageProps> = ({ onNavigate }) => {
  const { isAuthenticated, openAuthModal } = useAuth();
  const [mistakes, setMistakes] = useState<Mistake[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedType, setSelectedType] = useState<string>("");
  const [resolutionFilter, setResolutionFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newType, setNewType] = useState<MistakeType>("LOGIC_ERROR");
  const [newDescription, setNewDescription] = useState("");
  const [newCorrection, setNewCorrection] = useState("");
  const [modalSubmitting, setModalSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const loadMistakes = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (selectedType) params.append("mistake_type", selectedType);
    if (resolutionFilter === "unresolved") params.append("is_resolved", "false");
    if (resolutionFilter === "resolved") params.append("is_resolved", "true");
    if (searchQuery.trim()) params.append("search", searchQuery.trim());
    params.append("limit", "100");

    try {
      const res = await fetchApi<{ items: Mistake[]; total: number }>(
        `/api/v1/mistakes?${params.toString()}`
      );
      setMistakes(res.data.items || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load mistakes.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, selectedType, resolutionFilter, searchQuery]);

  useEffect(() => {
    loadMistakes();
  }, [loadMistakes]);

  const toggleResolved = async (mistake: Mistake) => {
    try {
      await fetchApi<Mistake>(`/api/v1/mistakes/${mistake.public_id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_resolved: !mistake.is_resolved }),
      });
      setMistakes((prev) =>
        prev.map((m) =>
          m.id === mistake.id
            ? { ...m, is_resolved: !m.is_resolved, resolved_at: !m.is_resolved ? new Date().toISOString() : undefined }
            : m
        )
      );
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to update status.");
    }
  };

  const deleteMistake = async (publicId: string) => {
    if (!confirm("Are you sure you want to remove this mistake log?")) return;
    try {
      await fetchApi(`/api/v1/mistakes/${publicId}`, {
        method: "DELETE",
      });
      setMistakes((prev) => prev.filter((m) => m.public_id !== publicId));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete mistake.");
    }
  };

  const handleCreateMistake = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newDescription.trim()) {
      setModalError("Title and description are required.");
      return;
    }

    setModalSubmitting(true);
    setModalError(null);

    try {
      const res = await fetchApi<Mistake>("/api/v1/mistakes", {
        method: "POST",
        body: JSON.stringify({
          title: newTitle.trim(),
          mistake_type: newType,
          description: newDescription.trim(),
          correction: newCorrection.trim() || undefined,
        }),
      });

      setMistakes((prev) => [res.data, ...prev]);
      setShowCreateModal(false);
      setNewTitle("");
      setNewDescription("");
      setNewCorrection("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create mistake entry.";
      setModalError(msg);
    } finally {
      setModalSubmitting(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <main id="main-content" style={{ flex: 1, maxWidth: "800px", margin: "var(--space-12) auto", padding: "0 var(--space-6)", textAlign: "center" }}>
        <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-xl)", padding: "var(--space-10) var(--space-8)" }}>
          <div style={{ fontSize: "3rem", marginBottom: "var(--space-4)" }}>📓</div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: "var(--space-3)" }}>
            Mistake Notebook
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "1rem", lineHeight: 1.6, maxWidth: "520px", margin: "0 auto var(--space-6) auto" }}>
            Sign in to log errors, identify recurrent patterns (concept gaps, edge cases, off-by-one errors), and turn mistakes into permanent learning.
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
            Sign In to Open Notebook
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
            Mistake Notebook
          </h1>
          <p style={{ color: "var(--text-secondary)", margin: 0, fontSize: "0.9375rem" }}>
            Categorize cognitive errors, logic lapses, and runtime bottlenecks to avoid repeating them in future interviews.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          style={{
            backgroundColor: "var(--brand-primary)",
            color: "#ffffff",
            border: "none",
            padding: "var(--space-2) var(--space-5)",
            borderRadius: "var(--radius-md)",
            fontWeight: 600,
            cursor: "pointer",
            fontSize: "0.875rem",
            display: "flex",
            alignItems: "center",
            gap: "var(--space-2)",
          }}
        >
          <span>+</span> Record New Mistake
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div
        style={{
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-lg)",
          padding: "var(--space-4)",
          marginBottom: "var(--space-6)",
          display: "flex",
          flexWrap: "wrap",
          gap: "var(--space-4)",
          alignItems: "center",
        }}
      >
        <div style={{ flex: 1, minWidth: "220px" }}>
          <input
            type="search"
            placeholder="Search mistakes by keyword..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
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

        <div style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap" }}>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            style={{
              padding: "var(--space-2) var(--space-3)",
              backgroundColor: "var(--bg-primary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              color: "var(--text-primary)",
              fontSize: "0.875rem",
            }}
            aria-label="Filter by mistake category"
          >
            <option value="">All Categories</option>
            {MISTAKE_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.replace(/_/g, " ")}
              </option>
            ))}
          </select>

          <select
            value={resolutionFilter}
            onChange={(e) => setResolutionFilter(e.target.value)}
            style={{
              padding: "var(--space-2) var(--space-3)",
              backgroundColor: "var(--bg-primary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              color: "var(--text-primary)",
              fontSize: "0.875rem",
            }}
            aria-label="Filter by resolution state"
          >
            <option value="all">All Resolutions</option>
            <option value="unresolved">Open Only</option>
            <option value="resolved">Resolved Only</option>
          </select>
        </div>
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

      {/* Mistake Cards List */}
      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "var(--space-12) 0" }}>
          <LoadingSpinner size="lg" />
        </div>
      ) : mistakes.length === 0 ? (
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-xl)",
            padding: "var(--space-12) var(--space-6)",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "2.5rem", marginBottom: "var(--space-3)" }}>💡</div>
          <h3 style={{ fontSize: "1.125rem", fontWeight: 700, margin: "0 0 var(--space-2) 0" }}>
            No mistakes found
          </h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", margin: "0 0 var(--space-4) 0" }}>
            {searchQuery || selectedType || resolutionFilter !== "all"
              ? "Try adjusting your filters or search terms."
              : "Whenever you encounter a tricky edge case or logic bug, document it here for review."}
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            style={{
              backgroundColor: "var(--brand-primary)",
              color: "#ffffff",
              border: "none",
              padding: "var(--space-2) var(--space-5)",
              borderRadius: "var(--radius-md)",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Record Your First Mistake
          </button>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          {mistakes.map((m) => (
            <div
              key={m.id}
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-lg)",
                padding: "var(--space-5) var(--space-6)",
                opacity: m.is_resolved ? 0.75 : 1,
                transition: "opacity 0.2s ease",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "var(--space-4)", marginBottom: "var(--space-2)" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap", marginBottom: "var(--space-1)" }}>
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
                      {m.mistake_type.replace(/_/g, " ")}
                    </span>
                    {m.is_resolved ? (
                      <span
                        style={{
                          fontSize: "0.6875rem",
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: "var(--radius-sm)",
                          backgroundColor: "var(--status-success-bg)",
                          color: "var(--status-success)",
                          border: "1px solid var(--status-success)",
                        }}
                      >
                        ✓ RESOLVED
                      </span>
                    ) : (
                      <span
                        style={{
                          fontSize: "0.6875rem",
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: "var(--radius-sm)",
                          backgroundColor: "rgba(234, 179, 8, 0.15)",
                          color: "var(--status-warning)",
                          border: "1px solid var(--status-warning)",
                        }}
                      >
                        OPEN
                      </span>
                    )}
                    {m.problem_title && (
                      <button
                        onClick={() => onNavigate(`/problems/${m.problem_slug}`)}
                        style={{
                          background: "none",
                          border: "none",
                          padding: 0,
                          fontSize: "0.75rem",
                          color: "var(--brand-primary)",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        Problem: {m.problem_title}
                      </button>
                    )}
                  </div>
                  <h2 style={{ fontSize: "1.125rem", fontWeight: 700, margin: 0 }}>
                    {m.title}
                  </h2>
                </div>

                <div style={{ display: "flex", gap: "var(--space-2)" }}>
                  <button
                    onClick={() => toggleResolved(m)}
                    style={{
                      background: m.is_resolved ? "var(--bg-tertiary)" : "var(--status-success-bg)",
                      border: `1px solid ${m.is_resolved ? "var(--border-subtle)" : "var(--status-success)"}`,
                      color: m.is_resolved ? "var(--text-secondary)" : "var(--status-success)",
                      padding: "4px 10px",
                      borderRadius: "var(--radius-md)",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    {m.is_resolved ? "Reopen" : "Mark Resolved"}
                  </button>
                  <button
                    onClick={() => deleteMistake(m.public_id)}
                    style={{
                      background: "none",
                      border: "1px solid var(--border-subtle)",
                      color: "var(--status-danger)",
                      padding: "4px 8px",
                      borderRadius: "var(--radius-md)",
                      fontSize: "0.75rem",
                      cursor: "pointer",
                    }}
                    title="Delete mistake"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* Description */}
              <p style={{ margin: "var(--space-2) 0", fontSize: "0.875rem", color: "var(--text-primary)", lineHeight: 1.6, whiteSpace: "pre-line" }}>
                {m.description}
              </p>

              {/* Correction / Takeaway */}
              {m.correction && (
                <div
                  style={{
                    backgroundColor: "var(--bg-tertiary)",
                    borderLeft: "3px solid var(--brand-primary)",
                    padding: "var(--space-2) var(--space-4)",
                    borderRadius: "0 var(--radius-sm) var(--radius-sm) 0",
                    marginTop: "var(--space-3)",
                  }}
                >
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--brand-primary)", textTransform: "uppercase" }}>
                    Solution & Takeaway:
                  </span>
                  <p style={{ margin: "2px 0 0 0", fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.5, whiteSpace: "pre-line" }}>
                    {m.correction}
                  </p>
                </div>
              )}

              <div style={{ marginTop: "var(--space-3)", fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                Recorded: {new Date(m.created_at).toLocaleString()}
                {m.resolved_at && ` • Resolved: ${new Date(m.resolved_at).toLocaleString()}`}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
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
              maxWidth: "600px",
              width: "100%",
              padding: "var(--space-6)",
              boxSizing: "border-box",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
              <h2 id="modal-title" style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>
                Record Mistake
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: "1.25rem", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            {modalError && (
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
                {modalError}
              </div>
            )}

            <form onSubmit={handleCreateMistake}>
              <div style={{ marginBottom: "var(--space-4)" }}>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, marginBottom: "4px" }}>
                  Title / Concept Summary *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Off-by-one error in binary search right pointer"
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
                  Mistake Category *
                </label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value as MistakeType)}
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
                  {MISTAKE_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: "var(--space-4)" }}>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, marginBottom: "4px" }}>
                  What went wrong? (Description) *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Explain the cognitive gap, assumptions made, or missed edge case..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
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

              <div style={{ marginBottom: "var(--space-6)" }}>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, marginBottom: "4px" }}>
                  Correction / Rule of Thumb
                </label>
                <textarea
                  rows={2}
                  placeholder="What is the mental model to remember next time?"
                  value={newCorrection}
                  onChange={(e) => setNewCorrection(e.target.value)}
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
                  onClick={() => setShowCreateModal(false)}
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
                  disabled={modalSubmitting}
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
                  {modalSubmitting ? "Saving..." : "Save to Notebook"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
};
