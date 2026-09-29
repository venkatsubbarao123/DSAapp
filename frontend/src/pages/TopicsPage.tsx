import React, { useState, useEffect } from "react";
import { fetchApi } from "../services/apiClient.ts";
import { PaginatedData, TopicDetail, TopicSummary } from "../types/curriculum.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";

interface TopicsPageProps {
  topicId?: string;
  onNavigate: (path: string) => void;
}

export const TopicsPage: React.FC<TopicsPageProps> = ({ topicId, onNavigate }) => {
  const [topics, setTopics] = useState<TopicSummary[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<TopicDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    if (topicId) {
      // Fetch single topic with subtopics
      fetchApi<TopicDetail>(`/api/v1/topics/${topicId}`)
        .then((res) => {
          if (isMounted) setSelectedTopic(res.data);
        })
        .catch((err) => {
          if (isMounted) setError(err.message || "Failed to load topic details.");
        })
        .finally(() => {
          if (isMounted) setLoading(false);
        });
    } else {
      // Fetch all topics
      fetchApi<PaginatedData<TopicSummary>>("/api/v1/topics?page=1&page_size=50")
        .then((res) => {
          if (isMounted) setTopics(res.data?.items || []);
        })
        .catch((err) => {
          if (isMounted) setError(err.message || "Failed to load topics.");
        })
        .finally(() => {
          if (isMounted) setLoading(false);
        });
    }

    return () => {
      isMounted = false;
    };
  }, [topicId]);

  if (loading) {
    return (
      <main id="main-content" style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center" }}>
        <LoadingSpinner size="lg" />
      </main>
    );
  }

  // --- Single Topic Detail View ---
  if (topicId && selectedTopic) {
    return (
      <main
        id="main-content"
        style={{
          flex: 1,
          maxWidth: "1000px",
          margin: "0 auto",
          padding: "var(--space-8) var(--space-6)",
          width: "100%",
          boxSizing: "border-box",
        }}
      >
        <button
          onClick={() => onNavigate("/topics")}
          style={{
            background: "none",
            border: "none",
            color: "var(--brand-primary)",
            fontWeight: 600,
            fontSize: "0.875rem",
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: "var(--space-1)",
            marginBottom: "var(--space-6)",
            padding: 0,
          }}
        >
          ← Back to All Topics
        </button>

        <div style={{ marginBottom: "var(--space-8)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", marginBottom: "var(--space-2)" }}>
            <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: 0 }}>
              {selectedTopic.title}
            </h1>
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                padding: "2px 8px",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "var(--bg-tertiary)",
                color: "var(--brand-primary)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              {selectedTopic.difficulty}
            </span>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "1rem", lineHeight: 1.6, margin: 0 }}>
            {selectedTopic.description}
          </p>
        </div>

        <section>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "var(--space-4)" }}>
            Subtopics & Learning Modules
          </h2>

          {selectedTopic.subtopics.length === 0 ? (
            <p style={{ color: "var(--text-muted)" }}>No subtopics registered under this topic yet.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
              {selectedTopic.subtopics.map((st) => (
                <div
                  key={st.id}
                  style={{
                    backgroundColor: "var(--bg-secondary)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-lg)",
                    padding: "var(--space-6)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: "var(--space-4)",
                  }}
                >
                  <div>
                    <h3 style={{ fontSize: "1.125rem", fontWeight: 600, margin: "0 0 var(--space-1) 0" }}>
                      {st.title}
                    </h3>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", margin: 0 }}>
                      {st.description}
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: "var(--space-3)" }}>
                    <button
                      onClick={() => onNavigate(`/problems?topic_slug=${selectedTopic.slug}`)}
                      style={{
                        backgroundColor: "var(--brand-primary)",
                        color: "#ffffff",
                        border: "none",
                        borderRadius: "var(--radius-md)",
                        padding: "var(--space-2) var(--space-4)",
                        fontSize: "0.8125rem",
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      Practice Problems
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    );
  }

  // --- All Topics Directory View ---
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
      <section style={{ marginBottom: "var(--space-8)" }}>
        <h1
          style={{
            fontSize: "2.25rem",
            fontWeight: 800,
            letterSpacing: "-0.025em",
            marginBottom: "var(--space-2)",
          }}
        >
          Data Structure & Algorithmic Topics
        </h1>
        <p style={{ fontSize: "1.0625rem", color: "var(--text-secondary)", margin: 0 }}>
          Explore foundational topics structured systematically from memory layouts to graph traversals.
        </p>
      </section>

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

      {topics.length === 0 ? (
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-8)",
            textAlign: "center",
          }}
        >
          <p style={{ color: "var(--text-muted)" }}>No topics found.</p>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
            gap: "var(--space-6)",
          }}
        >
          {topics.map((t) => (
            <div
              key={t.id}
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-lg)",
                padding: "var(--space-6)",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                gap: "var(--space-4)",
              }}
            >
              <div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "var(--space-2)" }}>
                  <span
                    style={{
                      fontSize: "0.6875rem",
                      fontWeight: 600,
                      padding: "2px 6px",
                      borderRadius: "var(--radius-sm)",
                      backgroundColor: "var(--bg-tertiary)",
                      color: "var(--brand-primary)",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    {t.difficulty}
                  </span>
                  {t.access_level === "PREMIUM" && (
                    <span
                      style={{
                        fontSize: "0.6875rem",
                        fontWeight: 700,
                        padding: "1px 6px",
                        borderRadius: "var(--radius-sm)",
                        backgroundColor: "rgba(234, 179, 8, 0.2)",
                        color: "var(--status-warning)",
                      }}
                    >
                      PRO
                    </span>
                  )}
                </div>
                <h3 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 var(--space-2) 0" }}>
                  {t.title}
                </h3>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", margin: 0, lineHeight: 1.5 }}>
                  {t.description}
                </p>
              </div>

              <div style={{ display: "flex", gap: "var(--space-2)", marginTop: "var(--space-2)" }}>
                <button
                  onClick={() => onNavigate(`/topics/${t.slug}`)}
                  style={{
                    backgroundColor: "var(--brand-primary)",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "var(--radius-md)",
                    padding: "var(--space-2) var(--space-4)",
                    fontSize: "0.8125rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Explore Topic
                </button>
                <button
                  onClick={() => onNavigate(`/problems?topic_slug=${t.slug}`)}
                  style={{
                    background: "none",
                    color: "var(--text-primary)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    padding: "var(--space-2) var(--space-4)",
                    fontSize: "0.8125rem",
                    fontWeight: 500,
                    cursor: "pointer",
                  }}
                >
                  Problems
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
};
