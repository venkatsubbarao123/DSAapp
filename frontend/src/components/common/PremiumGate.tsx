import React from "react";

interface PremiumGateProps {
  contentType?: "problem" | "lesson" | "topic";
  onUpgrade: () => void;
}

export const PremiumGate: React.FC<PremiumGateProps> = ({
  contentType = "problem",
  onUpgrade,
}) => {
  return (
    <div
      role="region"
      aria-label="Premium Content Gate"
      style={{
        backgroundColor: "var(--bg-secondary)",
        border: "1px solid var(--status-warning)",
        borderRadius: "var(--radius-xl)",
        padding: "var(--space-8)",
        textAlign: "center",
        maxWidth: "600px",
        margin: "var(--space-8) auto",
        boxShadow: "0 10px 25px -5px rgba(234, 179, 8, 0.15)",
      }}
    >
      <div
        style={{
          width: "48px",
          height: "48px",
          borderRadius: "var(--radius-full)",
          backgroundColor: "rgba(234, 179, 8, 0.15)",
          color: "var(--status-warning)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          margin: "0 auto var(--space-4)",
          fontSize: "1.5rem",
        }}
      >
        ★
      </div>
      <h3
        style={{
          fontSize: "1.25rem",
          fontWeight: 700,
          color: "var(--text-primary)",
          marginBottom: "var(--space-2)",
        }}
      >
        DSAapp Pro {contentType.charAt(0).toUpperCase() + contentType.slice(1)}
      </h3>
      <p
        style={{
          color: "var(--text-secondary)",
          fontSize: "0.875rem",
          lineHeight: 1.6,
          marginBottom: "var(--space-6)",
        }}
      >
        This {contentType} is part of our comprehensive Pro curriculum. Upgrade to
        gain immediate access to advanced algorithms, hints, and structured explanations.
      </p>
      <button
        onClick={onUpgrade}
        style={{
          backgroundColor: "var(--brand-primary)",
          color: "#ffffff",
          border: "none",
          borderRadius: "var(--radius-md)",
          padding: "var(--space-3) var(--space-6)",
          fontWeight: 600,
          fontSize: "0.875rem",
          cursor: "pointer",
          display: "inline-flex",
          alignItems: "center",
          gap: "var(--space-2)",
          transition: "opacity 0.15s ease",
        }}
      >
        <span>Upgrade to Pro (₹999/yr)</span>
        <span>→</span>
      </button>
    </div>
  );
};
