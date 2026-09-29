import React, { useState } from "react";
import { VISUALIZER_CATALOG, getVisualizerFrames } from "../features/visualizers/registry.ts";
import { VisualizerMetadata, VisualizerType } from "../features/visualizers/types.ts";
import { VisualizerPlayer } from "../features/visualizers/VisualizerPlayer.tsx";

interface VisualizersPageProps {
  onNavigate?: (path: string) => void;
  initialType?: VisualizerType;
}

export const VisualizersPage: React.FC<VisualizersPageProps> = ({
  initialType = "binary-search",
}) => {
  const [selectedType, setSelectedType] = useState<VisualizerType>(initialType);
  const [customTarget, setCustomTarget] = useState<number>(23);

  const activeMetadata: VisualizerMetadata =
    VISUALIZER_CATALOG.find((v) => v.id === selectedType) || VISUALIZER_CATALOG[0];

  const frames = getVisualizerFrames(selectedType, { target: customTarget });

  const categories = ["All", "Fundamentals", "Algorithms", "Trees & Graphs", "Patterns"];
  const [activeCategory, setActiveCategory] = useState("All");

  const filteredCatalog =
    activeCategory === "All"
      ? VISUALIZER_CATALOG
      : VISUALIZER_CATALOG.filter((v) => v.category === activeCategory);

  return (
    <main
      style={{
        maxWidth: "1280px",
        margin: "0 auto",
        padding: "var(--space-8) var(--space-6)",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-8)",
      }}
    >
      {/* Title Header */}
      <div>
        <h1 style={{ fontSize: "2rem", margin: 0, color: "var(--text-primary)" }}>
          DSA Algorithm & Structure Visualizers
        </h1>
        <p style={{ color: "var(--text-secondary)", margin: "var(--space-2) 0 0 0" }}>
          Deterministic interactive state visualizers for key data structures and algorithmic paradigms.
        </p>
      </div>

      {/* Category Pills */}
      <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            style={{
              padding: "6px 14px",
              borderRadius: "var(--radius-full)",
              fontSize: "0.85rem",
              fontWeight: 600,
              backgroundColor: activeCategory === cat ? "var(--brand-primary)" : "var(--bg-tertiary)",
              color: activeCategory === cat ? "#ffffff" : "var(--text-secondary)",
              border: "1px solid var(--border-subtle)",
              cursor: "pointer",
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "280px 1fr",
          gap: "var(--space-6)",
          alignItems: "start",
        }}
      >
        {/* Visualizer Selector Sidebar */}
        <div
          style={{
            backgroundColor: "var(--bg-card)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-4)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-2)",
            maxHeight: "650px",
            overflowY: "auto",
          }}
        >
          <span style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 700, padding: "0 8px 4px 8px" }}>
            Select Visualizer ({filteredCatalog.length})
          </span>
          {filteredCatalog.map((v) => {
            const isSelected = v.id === selectedType;
            return (
              <button
                key={v.id}
                onClick={() => setSelectedType(v.id)}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "flex-start",
                  padding: "10px 12px",
                  borderRadius: "var(--radius-md)",
                  border: isSelected ? "1px solid var(--border-focus)" : "1px solid transparent",
                  backgroundColor: isSelected ? "var(--brand-glow)" : "transparent",
                  color: isSelected ? "var(--text-primary)" : "var(--text-secondary)",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.15s ease",
                }}
              >
                <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>{v.title}</span>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{v.timeComplexity}</span>
              </button>
            );
          })}
        </div>

        {/* Visualizer Canvas Area */}
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          {/* Optional parameters for search / target based visualizers */}
          {(selectedType === "binary-search" || selectedType === "array" || selectedType === "two-pointers" || selectedType === "bst") && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-3)",
                backgroundColor: "var(--bg-secondary)",
                padding: "var(--space-3) var(--space-4)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <label htmlFor="target-input" style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                Target Value (0-99):
              </label>
              <input
                id="target-input"
                type="number"
                min={0}
                max={99}
                value={customTarget}
                onChange={(e) => setCustomTarget(Number(e.target.value))}
                style={{
                  width: "80px",
                  padding: "6px 10px",
                  backgroundColor: "var(--bg-tertiary)",
                  border: "1px solid var(--border-muted)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "0.9rem",
                }}
              />
            </div>
          )}

          <VisualizerPlayer
            metadata={activeMetadata}
            frames={frames}
            onReset={() => {}}
          />
        </div>
      </div>
    </main>
  );
};
