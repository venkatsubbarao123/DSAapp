import React from "react";

interface NotFoundPageProps {
  onNavigate: (path: string) => void;
}

export const NotFoundPage: React.FC<NotFoundPageProps> = ({ onNavigate }) => {
  return (
    <main
      role="main"
      style={{
        maxWidth: "600px",
        margin: "var(--space-12) auto",
        padding: "var(--space-8) var(--space-6)",
        textAlign: "center",
      }}
    >
      <div
        style={{
          fontSize: "4rem",
          fontWeight: 800,
          color: "var(--text-muted)",
          fontFamily: "var(--font-mono)",
          lineHeight: 1,
          marginBottom: "var(--space-4)",
        }}
      >
        404
      </div>
      <h1
        style={{
          fontSize: "1.5rem",
          fontWeight: 700,
          marginBottom: "var(--space-2)",
          color: "var(--text-primary)",
        }}
      >
        Page Not Found
      </h1>
      <p
        style={{
          color: "var(--text-secondary)",
          fontSize: "0.9375rem",
          marginBottom: "var(--space-6)",
          lineHeight: 1.6,
        }}
      >
        The requested resource does not exist or has been moved to a new route.
      </p>
      <button
        onClick={() => onNavigate("/")}
        style={{
          backgroundColor: "var(--brand-primary)",
          color: "#ffffff",
          border: "none",
          borderRadius: "var(--radius-md)",
          padding: "var(--space-3) var(--space-6)",
          fontSize: "0.875rem",
          fontWeight: 600,
          cursor: "pointer",
          transition: "background-color 0.15s ease",
        }}
      >
        Return to Overview
      </button>
    </main>
  );
};
