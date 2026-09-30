import React, { useState, useEffect } from "react";
import { fetchApi } from "../services/apiClient.ts";
import { PaginatedData, ProblemDifficulty, ProblemSummary } from "../types/curriculum.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";

interface ProblemsPageProps {
  onNavigate: (path: string) => void;
  initialTopicSlug?: string;
}

export const ProblemsPage: React.FC<ProblemsPageProps> = ({ onNavigate, initialTopicSlug }) => {
  const getInitialTopic = () => {
    if (initialTopicSlug) return initialTopicSlug;
    if (typeof window !== "undefined" && window.location.search) {
      const p = new URLSearchParams(window.location.search);
      return p.get("topic_slug") || p.get("topic") || "";
    }
    return "";
  };

  const [problems, setProblems] = useState<ProblemSummary[]>([]);
  const [topics, setTopics] = useState<Array<{ id: string; slug: string; title: string }>>([]);
  const [selectedTopicSlug, setSelectedTopicSlug] = useState<string>(getInitialTopic());
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [difficultyFilter, setDifficultyFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [debouncedSearch, setDebouncedSearch] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Sync initialTopicSlug if prop changes
  useEffect(() => {
    if (initialTopicSlug !== undefined) {
      setSelectedTopicSlug(initialTopicSlug);
      setPage(1);
    }
  }, [initialTopicSlug]);

  // Load topics list for the topic filter dropdown
  useEffect(() => {
    fetchApi<PaginatedData<{ id: string; slug: string; title: string }>>("/api/v1/topics?page=1&page_size=100")
      .then((res) => {
        if (res.data?.items) {
          setTopics(res.data.items);
        }
      })
      .catch(() => {});
  }, []);

  // Debounce search input
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedSearch(searchQuery), 300);
    return () => clearTimeout(handler);
  }, [searchQuery]);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", "20");

    if (difficultyFilter !== "ALL") {
      params.set("difficulty", difficultyFilter);
    }
    if (debouncedSearch.trim()) {
      params.set("search", debouncedSearch.trim());
    }
    if (selectedTopicSlug) {
      params.set("topic_slug", selectedTopicSlug);
    }

    fetchApi<PaginatedData<ProblemSummary>>(`/api/v1/problems?${params.toString()}`)
      .then((res) => {
        if (!isMounted) return;
        setProblems(res.data?.items || []);
        setTotal(res.data?.total || 0);
        setTotalPages(res.data?.total_pages || 1);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || "Failed to load problems.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [page, difficultyFilter, debouncedSearch, selectedTopicSlug]);

  const difficultyColors = {
    EASY: "var(--status-success)",
    MEDIUM: "var(--status-warning)",
    HARD: "var(--status-danger)",
    EXPERT: "#a855f7",
  };

  return (
    <main
      id="main-content"
      style={{
        flex: 1,
        maxWidth: "1100px",
        margin: "0 auto",
        padding: "var(--space-8) var(--space-6)",
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      <header style={{ marginBottom: "var(--space-8)" }}>
        <h1 style={{ fontSize: "2.25rem", fontWeight: 800, margin: "0 0 var(--space-2) 0", letterSpacing: "-0.025em" }}>
          Algorithmic Problem Directory
        </h1>
        <p style={{ fontSize: "1.0625rem", color: "var(--text-secondary)", margin: 0 }}>
          Rigorous problem specifications classified by difficulty, algorithmic patterns, and data structures.
        </p>
      </header>

      {/* Filter and Search Bar */}
      <div
        style={{
          display: "flex",
          gap: "var(--space-4)",
          flexWrap: "wrap",
          marginBottom: "var(--space-4)",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap", alignItems: "center" }}>
          {/* Difficulty Filter Tabs */}
          <div style={{ display: "flex", gap: "var(--space-2)" }}>
            {["ALL", "EASY", "MEDIUM", "HARD"].map((diff) => (
              <button
                key={diff}
                onClick={() => {
                  setDifficultyFilter(diff);
                  setPage(1);
                }}
                style={{
                  backgroundColor: difficultyFilter === diff ? "var(--brand-primary)" : "var(--bg-secondary)",
                  color: difficultyFilter === diff ? "#ffffff" : "var(--text-secondary)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-md)",
                  padding: "6px 14px",
                  fontSize: "0.8125rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {diff}
              </button>
            ))}
          </div>

          {/* Topic Dropdown Filter */}
          <select
            value={selectedTopicSlug}
            onChange={(e) => {
              setSelectedTopicSlug(e.target.value);
              setPage(1);
            }}
            aria-label="Filter by Topic"
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              padding: "6px 12px",
              fontSize: "0.8125rem",
              fontWeight: 600,
              color: "var(--text-primary)",
              cursor: "pointer",
              outline: "none",
            }}
          >
            <option value="">All Topics (415)</option>
            {topics.map((t) => (
              <option key={t.id} value={t.slug}>
                {t.title}
              </option>
            ))}
          </select>
        </div>

        {/* Search Input */}
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            setPage(1);
          }}
          placeholder="Search problems by title, topic, or tag..."
          style={{
            minWidth: "280px",
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-md)",
            padding: "8px 14px",
            color: "var(--text-primary)",
            fontSize: "0.875rem",
            outline: "none",
          }}
        />
      </div>

      {/* Active Filter Chips & Result Counter */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "var(--space-2)",
          marginBottom: "var(--space-4)",
          fontSize: "0.8125rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
          <span style={{ color: "var(--text-muted)" }}>
            Showing <strong>{problems.length}</strong> of <strong>{total}</strong> problems
            {selectedTopicSlug ? ` in ${topics.find((t) => t.slug === selectedTopicSlug)?.title || selectedTopicSlug}` : ""}
            {difficultyFilter !== "ALL" ? ` (${difficultyFilter})` : ""}
          </span>

          {selectedTopicSlug && (
            <span
              style={{
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                padding: "2px 8px",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              Topic: {topics.find((t) => t.slug === selectedTopicSlug)?.title || selectedTopicSlug}
              <button
                onClick={() => {
                  setSelectedTopicSlug("");
                  setPage(1);
                }}
                style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: 0 }}
              >
                ✕
              </button>
            </span>
          )}

          {difficultyFilter !== "ALL" && (
            <span
              style={{
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                padding: "2px 8px",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              Difficulty: {difficultyFilter}
              <button
                onClick={() => {
                  setDifficultyFilter("ALL");
                  setPage(1);
                }}
                style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: 0 }}
              >
                ✕
              </button>
            </span>
          )}

          {debouncedSearch && (
            <span
              style={{
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                padding: "2px 8px",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              Query: &quot;{debouncedSearch}&quot;
              <button
                onClick={() => {
                  setSearchQuery("");
                  setPage(1);
                }}
                style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: 0 }}
              >
                ✕
              </button>
            </span>
          )}
        </div>

        {(selectedTopicSlug || difficultyFilter !== "ALL" || debouncedSearch) && (
          <button
            onClick={() => {
              setSelectedTopicSlug("");
              setDifficultyFilter("ALL");
              setSearchQuery("");
              setPage(1);
            }}
            style={{
              background: "none",
              border: "none",
              color: "var(--brand-primary)",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "0.8125rem",
              padding: 0,
            }}
          >
            Clear All Filters
          </button>
        )}
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

      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "var(--space-12)" }}>
          <LoadingSpinner size="lg" />
        </div>
      ) : problems.length === 0 ? (
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-10)",
            textAlign: "center",
          }}
        >
          <p style={{ color: "var(--text-primary)", fontWeight: 600, fontSize: "1.125rem", marginBottom: "var(--space-2)" }}>
            No matching problems found
          </p>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginBottom: "var(--space-4)" }}>
            Try relaxing your difficulty or topic filters, or searching with different keywords.
          </p>
          <button
            onClick={() => {
              setSelectedTopicSlug("");
              setDifficultyFilter("ALL");
              setSearchQuery("");
              setPage(1);
            }}
            style={{
              backgroundColor: "var(--brand-primary)",
              color: "#ffffff",
              border: "none",
              borderRadius: "var(--radius-md)",
              padding: "8px 16px",
              fontWeight: 600,
              fontSize: "0.875rem",
              cursor: "pointer",
            }}
          >
            Clear Filters
          </button>
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
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              textAlign: "left",
              fontSize: "0.875rem",
            }}
          >
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-muted)" }}>
                <th style={{ padding: "var(--space-4) var(--space-6)" }}>Title</th>
                <th style={{ padding: "var(--space-4)" }}>Difficulty</th>
                <th style={{ padding: "var(--space-4)" }}>Patterns / Tags</th>
                <th style={{ padding: "var(--space-4)" }}>Tier</th>
                <th style={{ padding: "var(--space-4) var(--space-6)", textAlign: "right" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {problems.map((p) => (
                <tr
                  key={p.id}
                  style={{
                    borderBottom: "1px solid var(--border-subtle)",
                    transition: "background-color 0.15s ease",
                  }}
                >
                  <td style={{ padding: "var(--space-4) var(--space-6)", fontWeight: 600 }}>
                    <button
                      onClick={() => onNavigate(`/problems/${p.slug}`)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "var(--text-primary)",
                        fontWeight: 600,
                        fontSize: "0.9375rem",
                        cursor: "pointer",
                        padding: 0,
                        textAlign: "left",
                      }}
                    >
                      {p.title}
                    </button>
                  </td>
                  <td style={{ padding: "var(--space-4)" }}>
                    <span
                      style={{
                        fontWeight: 700,
                        fontSize: "0.75rem",
                        color: difficultyColors[p.difficulty as ProblemDifficulty] || "var(--text-primary)",
                      }}
                    >
                      {p.difficulty}
                    </span>
                  </td>
                  <td style={{ padding: "var(--space-4)" }}>
                    <div style={{ display: "flex", gap: "var(--space-1)", flexWrap: "wrap" }}>
                      {p.patterns.slice(0, 1).map((pat) => (
                        <span
                          key={pat.id}
                          style={{
                            fontSize: "0.6875rem",
                            backgroundColor: "var(--bg-tertiary)",
                            color: "var(--brand-primary)",
                            padding: "2px 6px",
                            borderRadius: "var(--radius-sm)",
                            border: "1px solid var(--border-subtle)",
                          }}
                        >
                          {pat.name}
                        </span>
                      ))}
                      {p.tags.slice(0, 2).map((t) => (
                        <span
                          key={t.id}
                          style={{
                            fontSize: "0.6875rem",
                            backgroundColor: "var(--bg-tertiary)",
                            color: "var(--text-muted)",
                            padding: "2px 6px",
                            borderRadius: "var(--radius-sm)",
                          }}
                        >
                          {t.name}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td style={{ padding: "var(--space-4)" }}>
                    {p.access_level === "PREMIUM" ? (
                      <span
                        style={{
                          fontSize: "0.6875rem",
                          fontWeight: 700,
                          padding: "2px 6px",
                          borderRadius: "var(--radius-sm)",
                          backgroundColor: "rgba(234, 179, 8, 0.15)",
                          color: "var(--status-warning)",
                          border: "1px solid var(--status-warning)",
                        }}
                      >
                        PRO
                      </span>
                    ) : (
                      <span
                        style={{
                          fontSize: "0.6875rem",
                          fontWeight: 600,
                          color: "var(--text-muted)",
                        }}
                      >
                        FREE
                      </span>
                    )}
                  </td>
                  <td style={{ padding: "var(--space-4) var(--space-6)", textAlign: "right" }}>
                    <button
                      onClick={() => onNavigate(`/problems/${p.slug}`)}
                      style={{
                        backgroundColor: "var(--bg-tertiary)",
                        border: "1px solid var(--border-subtle)",
                        color: "var(--text-primary)",
                        borderRadius: "var(--radius-md)",
                        padding: "4px 12px",
                        fontSize: "0.8125rem",
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      Solve
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "var(--space-6)" }}>
          <button
            onClick={() => setPage((p) => Math.max(p - 1, 1))}
            disabled={page <= 1}
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              color: page <= 1 ? "var(--text-muted)" : "var(--text-primary)",
              padding: "6px 14px",
              borderRadius: "var(--radius-md)",
              cursor: page <= 1 ? "not-allowed" : "pointer",
              fontSize: "0.8125rem",
              fontWeight: 600,
            }}
          >
            ← Previous
          </button>
          <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            Page {page} of {totalPages} ({total} problems)
          </span>
          <button
            onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
            disabled={page >= totalPages}
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border-subtle)",
              color: page >= totalPages ? "var(--text-muted)" : "var(--text-primary)",
              padding: "6px 14px",
              borderRadius: "var(--radius-md)",
              cursor: page >= totalPages ? "not-allowed" : "pointer",
              fontSize: "0.8125rem",
              fontWeight: 600,
            }}
          >
            Next →
          </button>
        </div>
      )}
    </main>
  );
};
