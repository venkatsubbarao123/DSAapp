import React, { useState, useEffect } from "react";
import { fetchApi, APIClientError } from "../services/apiClient.ts";
import { LessonBlock, LessonDetail } from "../types/curriculum.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";
import { PremiumGate } from "../components/common/PremiumGate.tsx";

interface LessonPageProps {
  lessonId: string;
  onNavigate: (path: string) => void;
}

export const LessonPage: React.FC<LessonPageProps> = ({ lessonId, onNavigate }) => {
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isLocked, setIsLocked] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setIsLocked(false);
    setError(null);

    fetchApi<LessonDetail>(`/api/v1/lessons/${lessonId}`)
      .then((res) => {
        if (isMounted) setLesson(res.data);
      })
      .catch((err) => {
        if (!isMounted) return;
        if (err instanceof APIClientError && err.code === "HTTP_403") {
          setIsLocked(true);
        } else {
          setError(err.message || "Failed to load lesson.");
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [lessonId]);

  if (loading) {
    return (
      <main id="main-content" style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center" }}>
        <LoadingSpinner size="lg" />
      </main>
    );
  }

  if (isLocked) {
    return (
      <main id="main-content" style={{ flex: 1, padding: "var(--space-8) var(--space-6)" }}>
        <PremiumGate contentType="lesson" onUpgrade={() => onNavigate("/premium")} />
      </main>
    );
  }

  if (error || !lesson) {
    return (
      <main id="main-content" style={{ flex: 1, padding: "var(--space-8) var(--space-6)", maxWidth: "800px", margin: "0 auto" }}>
        <div
          role="alert"
          style={{
            backgroundColor: "var(--status-danger-bg)",
            border: "1px solid var(--status-danger)",
            color: "var(--status-danger)",
            padding: "var(--space-4)",
            borderRadius: "var(--radius-md)",
            marginBottom: "var(--space-4)",
          }}
        >
          {error || "Lesson not found."}
        </div>
        <button
          onClick={() => onNavigate("/topics")}
          style={{
            background: "none",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-primary)",
            padding: "var(--space-2) var(--space-4)",
            borderRadius: "var(--radius-md)",
            cursor: "pointer",
          }}
        >
          ← Return to Topics
        </button>
      </main>
    );
  }

  // Safe structured block renderer (immune to XSS, no raw HTML execution)
  const renderBlock = (block: LessonBlock, index: number) => {
    switch (block.type) {
      case "heading": {
        const HeadingTag = block.level === 1 ? "h1" : block.level === 2 ? "h2" : "h3";
        return (
          <HeadingTag
            key={index}
            style={{
              fontSize: block.level === 1 ? "1.75rem" : block.level === 2 ? "1.375rem" : "1.125rem",
              fontWeight: 700,
              marginTop: "var(--space-6)",
              marginBottom: "var(--space-3)",
              color: "var(--text-primary)",
            }}
          >
            {block.content}
          </HeadingTag>
        );
      }
      case "paragraph":
        return (
          <p
            key={index}
            style={{
              fontSize: "1rem",
              lineHeight: 1.7,
              color: "var(--text-secondary)",
              marginBottom: "var(--space-4)",
            }}
          >
            {block.content}
          </p>
        );
      case "code":
        return (
          <div
            key={index}
            style={{
              backgroundColor: "var(--bg-tertiary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              padding: "var(--space-4)",
              marginBottom: "var(--space-4)",
              overflowX: "auto",
            }}
          >
            {block.language && (
              <span
                style={{
                  display: "block",
                  fontSize: "0.6875rem",
                  fontFamily: "var(--font-mono)",
                  color: "var(--text-muted)",
                  marginBottom: "var(--space-2)",
                  textTransform: "uppercase",
                }}
              >
                {block.language}
              </span>
            )}
            <pre
              style={{
                margin: 0,
                fontFamily: "var(--font-mono)",
                fontSize: "0.875rem",
                lineHeight: 1.5,
                color: "var(--text-primary)",
              }}
            >
              <code>{block.content}</code>
            </pre>
          </div>
        );
      case "note":
      case "tip":
      case "warning":
      case "example": {
        const borderColors = {
          note: "var(--brand-primary)",
          tip: "var(--status-success)",
          warning: "var(--status-warning)",
          example: "var(--border-muted)",
        };
        const bgColors = {
          note: "rgba(59, 130, 246, 0.08)",
          tip: "rgba(34, 197, 94, 0.08)",
          warning: "rgba(234, 179, 8, 0.08)",
          example: "var(--bg-tertiary)",
        };
        return (
          <div
            key={index}
            style={{
              borderLeft: `4px solid ${borderColors[block.type]}`,
              backgroundColor: bgColors[block.type],
              padding: "var(--space-4)",
              borderRadius: "0 var(--radius-md) var(--radius-md) 0",
              marginBottom: "var(--space-4)",
              fontSize: "0.9375rem",
              lineHeight: 1.6,
              color: "var(--text-secondary)",
            }}
          >
            <strong style={{ display: "block", textTransform: "uppercase", fontSize: "0.75rem", marginBottom: "4px", color: borderColors[block.type] }}>
              {block.type}
            </strong>
            {block.content}
          </div>
        );
      }
      default:
        return (
          <p key={index} style={{ marginBottom: "var(--space-4)", color: "var(--text-secondary)" }}>
            {block.content}
          </p>
        );
    }
  };

  return (
    <main
      id="main-content"
      style={{
        flex: 1,
        maxWidth: "840px",
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
          marginBottom: "var(--space-6)",
          padding: 0,
        }}
      >
        ← Back to Topics
      </button>

      {/* Lesson Header */}
      <header style={{ marginBottom: "var(--space-8)", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "var(--space-6)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)" }}>
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
            {lesson.difficulty}
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            ⏱ {lesson.estimated_minutes} min read
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            v{lesson.version}
          </span>
        </div>
        <h1 style={{ fontSize: "2.25rem", fontWeight: 800, margin: "0 0 var(--space-3) 0", letterSpacing: "-0.02em" }}>
          {lesson.title}
        </h1>
        <p style={{ fontSize: "1.0625rem", color: "var(--text-secondary)", margin: 0, lineHeight: 1.6 }}>
          {lesson.summary}
        </p>
      </header>

      {/* Structured Content Blocks */}
      <article>{lesson.blocks.map(renderBlock)}</article>
    </main>
  );
};
