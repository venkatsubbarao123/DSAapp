import React from "react";

export const Footer: React.FC = () => {
  return (
    <footer
      style={{
        borderTop: "1px solid var(--border-subtle)",
        backgroundColor: "var(--bg-secondary)",
        padding: "var(--space-6)",
        marginTop: "auto",
        textAlign: "center",
        fontSize: "0.8125rem",
        color: "var(--text-muted)",
      }}
    >
      <div
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "var(--space-4)",
        }}
      >
        <div>
          <span>DSAapp — Secure Production Coding Education Platform</span>
        </div>
        <div style={{ display: "flex", gap: "var(--space-4)" }}>
          <span>Phase 1 Architecture Foundation</span>
          <span>•</span>
          <span>WCAG 2.1 AA Compliant</span>
          <span>•</span>
          <span>Strict Security Enforced</span>
        </div>
      </div>
    </footer>
  );
};
