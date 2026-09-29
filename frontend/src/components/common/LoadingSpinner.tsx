import React from "react";

interface LoadingSpinnerProps {
  label?: string;
  size?: "sm" | "md" | "lg";
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label = "Loading...",
  size = "md",
}) => {
  const pixelSize = size === "sm" ? "16px" : size === "lg" ? "36px" : "24px";

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "var(--space-2)",
      }}
    >
      <div
        style={{
          width: pixelSize,
          height: pixelSize,
          border: "2px solid var(--border-muted)",
          borderTopColor: "var(--brand-primary)",
          borderRadius: "var(--radius-full)",
          animation: "spin 0.8s linear infinite",
        }}
      />
      <span
        style={{
          fontSize: "0.875rem",
          color: "var(--text-secondary)",
        }}
      >
        {label}
      </span>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
