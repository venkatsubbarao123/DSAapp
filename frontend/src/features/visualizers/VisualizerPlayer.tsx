import React, { useEffect, useRef, useState } from "react";
import { VisualizerFrame, VisualizerMetadata } from "./types.ts";

interface VisualizerPlayerProps {
  metadata: VisualizerMetadata;
  frames: VisualizerFrame[];
  onReset?: () => void;
}

export const VisualizerPlayer: React.FC<VisualizerPlayerProps> = ({
  metadata,
  frames,
  onReset,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speedMultiplier, setSpeedMultiplier] = useState(1);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const totalSteps = frames.length;
  const currentFrame: VisualizerFrame = frames[currentStep] || {
    stepIndex: 0,
    description: "Ready",
    dataState: null,
  };

  // Auto-play interval
  useEffect(() => {
    if (isPlaying) {
      const delay = Math.max(250, 1000 / speedMultiplier);
      timerRef.current = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= totalSteps - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, delay);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, totalSteps, speedMultiplier]);

  const handleNext = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStep(0);
    if (onReset) onReset();
  };

  // Renderer helper for data states
  const renderVisualData = () => {
    const { id } = metadata;
    const { dataState, highlighted = [], activeIndices = [], pointers = {} } = currentFrame;

    if (!dataState) {
      return <div style={{ color: "var(--text-muted)" }}>No data available.</div>;
    }

    // 1. Array-like structures (Array, Sorting, Binary Search, Two Pointers, Sliding Window, Heap)
    if (Array.isArray(dataState)) {
      return (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "var(--space-4)" }}>
          {/* Pointers Row */}
          <div style={{ display: "flex", gap: "var(--space-3)", minHeight: "28px" }}>
            {dataState.map((_, idx) => {
              const ptrEntries = Object.entries(pointers).filter(([_, v]) => v === idx);
              return (
                <div
                  key={`ptr-${idx}`}
                  style={{
                    width: "48px",
                    textAlign: "center",
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    color: "var(--brand-primary)",
                  }}
                >
                  {ptrEntries.map(([k]) => k).join(", ")}
                </div>
              );
            })}
          </div>

          {/* Array Boxes */}
          <div style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap", justifyContent: "center" }}>
            {dataState.map((val: any, idx: number) => {
              const isHighlight = highlighted.includes(idx);
              const isActive = activeIndices.includes(idx);

              let bg = "var(--bg-tertiary)";
              let border = "1px solid var(--border-muted)";
              let textColor = "var(--text-primary)";

              if (isActive) {
                bg = "var(--status-success-bg)";
                border = "2px solid var(--status-success)";
                textColor = "var(--status-success)";
              } else if (isHighlight) {
                bg = "var(--brand-glow)";
                border = "2px solid var(--brand-primary)";
                textColor = "#ffffff";
              }

              return (
                <div
                  key={`cell-${idx}`}
                  style={{
                    width: "48px",
                    height: "54px",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    backgroundColor: bg,
                    border,
                    borderRadius: "var(--radius-md)",
                    transition: "all 0.2s ease",
                  }}
                >
                  <span style={{ fontSize: "1.1rem", fontWeight: 700, color: textColor }}>{val}</span>
                  <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", marginTop: "2px" }}>[{idx}]</span>
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    // 2. Stack Structure
    if (id === "stack" && Array.isArray(dataState)) {
      return (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
          <div
            style={{
              width: "160px",
              minHeight: "180px",
              border: "2px solid var(--border-focus)",
              borderTop: "none",
              borderRadius: "0 0 var(--radius-md) var(--radius-md)",
              padding: "var(--space-3)",
              display: "flex",
              flexDirection: "column-reverse",
              gap: "var(--space-2)",
              backgroundColor: "var(--bg-card)",
            }}
          >
            {dataState.map((val: any, idx: number) => (
              <div
                key={`stack-${idx}`}
                style={{
                  height: "36px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  backgroundColor: idx === dataState.length - 1 ? "var(--brand-glow)" : "var(--bg-tertiary)",
                  border: "1px solid var(--brand-primary)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontWeight: 600,
                }}
              >
                {val} {idx === dataState.length - 1 && " (Top)"}
              </div>
            ))}
          </div>
          <span style={{ marginTop: "var(--space-2)", fontSize: "0.8rem", color: "var(--text-muted)" }}>Stack Base</span>
        </div>
      );
    }

    // 3. Queue Structure
    if (id === "queue" && Array.isArray(dataState)) {
      return (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "var(--space-3)" }}>
          <span style={{ fontSize: "0.8rem", color: "var(--status-danger)" }}>OUT &lt;- Front</span>
          <div
            style={{
              display: "flex",
              gap: "var(--space-2)",
              padding: "var(--space-3)",
              border: "2px dashed var(--border-focus)",
              borderRadius: "var(--radius-md)",
              backgroundColor: "var(--bg-card)",
              minWidth: "240px",
              justifyContent: "center",
            }}
          >
            {dataState.map((val: any, idx: number) => (
              <div
                key={`queue-${idx}`}
                style={{
                  width: "44px",
                  height: "44px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  backgroundColor: "var(--bg-tertiary)",
                  border: "1px solid var(--brand-primary)",
                  borderRadius: "var(--radius-sm)",
                  fontWeight: 700,
                }}
              >
                {val}
              </div>
            ))}
          </div>
          <span style={{ fontSize: "0.8rem", color: "var(--status-success)" }}>Rear &lt;- IN</span>
        </div>
      );
    }

    // 4. Linked List Structure
    if (id === "linked-list" && Array.isArray(dataState)) {
      return (
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap", justifyContent: "center" }}>
          {dataState.map((node: any, idx: number) => {
            const isHighlight = highlighted.includes(node.id);
            return (
              <React.Fragment key={`ll-${node.id}`}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    border: isHighlight ? "2px solid var(--status-success)" : "1px solid var(--border-muted)",
                    borderRadius: "var(--radius-md)",
                    backgroundColor: isHighlight ? "var(--status-success-bg)" : "var(--bg-tertiary)",
                    overflow: "hidden",
                  }}
                >
                  <div style={{ padding: "8px 12px", fontWeight: 700, color: "var(--text-primary)" }}>{node.val}</div>
                  <div style={{ padding: "8px 8px", backgroundColor: "var(--bg-card)", borderLeft: "1px solid var(--border-subtle)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    {node.nextId !== null ? "•" : "null"}
                  </div>
                </div>
                {idx < dataState.length - 1 && (
                  <span style={{ color: "var(--brand-primary)", fontWeight: 700, fontSize: "1.2rem" }}>-&gt;</span>
                )}
              </React.Fragment>
            );
          })}
        </div>
      );
    }

    // 5. Binary Tree & BST (SVG visualizer)
    if ((id === "binary-tree" || id === "bst") && dataState.nodes) {
      return (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: "100%" }}>
          <svg width="400" height="220" style={{ overflow: "visible" }}>
            {/* Draw lines */}
            {dataState.nodes.map((n: any) => {
              const left = dataState.nodes.find((c: any) => c.id === n.leftId);
              const right = dataState.nodes.find((c: any) => c.id === n.rightId);
              return (
                <g key={`edges-${n.id}`}>
                  {left && <line x1={n.x} y1={n.y} x2={left.x} y2={left.y} stroke="var(--border-muted)" strokeWidth="2" />}
                  {right && <line x1={n.x} y1={n.y} x2={right.x} y2={right.y} stroke="var(--border-muted)" strokeWidth="2" />}
                </g>
              );
            })}

            {/* Draw nodes */}
            {dataState.nodes.map((n: any) => {
              const isHighlight = highlighted.includes(n.id);
              const isActive = activeIndices.includes(n.id);
              let fill = "var(--bg-tertiary)";
              let stroke = "var(--border-focus)";
              if (isActive) {
                fill = "var(--status-success)";
                stroke = "#ffffff";
              } else if (isHighlight) {
                fill = "var(--brand-primary)";
                stroke = "#ffffff";
              }
              return (
                <g key={`node-${n.id}`}>
                  <circle cx={n.x} cy={n.y} r="18" fill={fill} stroke={stroke} strokeWidth="2" />
                  <text x={n.x} y={n.y + 5} textAnchor="middle" fill="#ffffff" fontSize="12" fontWeight="700">
                    {n.val}
                  </text>
                </g>
              );
            })}
          </svg>

          {dataState.visitedOrder && (
            <div style={{ marginTop: "var(--space-3)", fontSize: "0.875rem", color: "var(--text-secondary)" }}>
              Visited Sequence: <strong style={{ color: "var(--brand-primary)" }}>[{dataState.visitedOrder.join(", ")}]</strong>
            </div>
          )}
        </div>
      );
    }

    // 6. Graph BFS / DFS / Recursion (Generic structured telemetry)
    return (
      <div style={{ backgroundColor: "var(--bg-tertiary)", padding: "var(--space-4)", borderRadius: "var(--radius-md)", width: "100%", maxWidth: "500px" }}>
        <pre style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize: "0.85rem", color: "var(--text-primary)" }}>
          {JSON.stringify(dataState, null, 2)}
        </pre>
      </div>
    );
  };

  return (
    <div
      style={{
        backgroundColor: "var(--bg-card)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--space-6)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-6)",
      }}
    >
      {/* Header Info */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "var(--space-4)" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
            <h2 style={{ fontSize: "1.4rem", margin: 0, color: "var(--text-primary)" }}>{metadata.title}</h2>
            <span
              style={{
                fontSize: "0.75rem",
                padding: "2px 8px",
                backgroundColor: "var(--bg-tertiary)",
                borderRadius: "var(--radius-full)",
                color: "var(--brand-primary)",
                border: "1px solid var(--border-muted)",
              }}
            >
              {metadata.category}
            </span>
          </div>
          <p style={{ margin: "var(--space-1) 0 0 0", color: "var(--text-secondary)", fontSize: "0.875rem" }}>
            {metadata.description}
          </p>
        </div>

        {/* Complexity Badges */}
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <div style={{ padding: "4px 10px", backgroundColor: "var(--bg-tertiary)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", display: "block" }}>Time</span>
            <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--status-info)" }}>{metadata.timeComplexity}</span>
          </div>
          <div style={{ padding: "4px 10px", backgroundColor: "var(--bg-tertiary)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", display: "block" }}>Space</span>
            <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--status-warning)" }}>{metadata.spaceComplexity}</span>
          </div>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div
        style={{
          minHeight: "240px",
          backgroundColor: "var(--bg-primary)",
          borderRadius: "var(--radius-md)",
          border: "1px solid var(--border-subtle)",
          padding: "var(--space-6)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {renderVisualData()}
      </div>

      {/* Step Explanation Banner */}
      <div
        style={{
          padding: "var(--space-3) var(--space-4)",
          backgroundColor: "var(--bg-secondary)",
          borderLeft: "4px solid var(--brand-primary)",
          borderRadius: "0 var(--radius-sm) var(--radius-sm) 0",
        }}
      >
        <span style={{ fontSize: "0.75rem", textTransform: "uppercase", fontWeight: 700, color: "var(--brand-primary)", display: "block" }}>
          Step {currentStep + 1} of {totalSteps}
        </span>
        <p style={{ margin: "var(--space-1) 0 0 0", color: "var(--text-primary)", fontSize: "0.95rem" }}>
          {currentFrame.description}
        </p>
      </div>

      {/* Playback Controls */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "var(--space-4)",
          borderTop: "1px solid var(--border-subtle)",
          paddingTop: "var(--space-4)",
        }}
      >
        {/* Step Buttons */}
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <button
            onClick={handleReset}
            style={{
              padding: "8px 14px",
              backgroundColor: "var(--bg-tertiary)",
              border: "1px solid var(--border-muted)",
              borderRadius: "var(--radius-sm)",
              color: "var(--text-primary)",
              cursor: "pointer",
              fontSize: "0.875rem",
            }}
          >
            Reset
          </button>
          <button
            onClick={handlePrev}
            disabled={currentStep === 0}
            style={{
              padding: "8px 14px",
              backgroundColor: "var(--bg-tertiary)",
              border: "1px solid var(--border-muted)",
              borderRadius: "var(--radius-sm)",
              color: "var(--text-primary)",
              cursor: currentStep === 0 ? "not-allowed" : "pointer",
              opacity: currentStep === 0 ? 0.5 : 1,
              fontSize: "0.875rem",
            }}
          >
            &lt; Prev
          </button>
          <button
            onClick={() => setIsPlaying((p) => !p)}
            style={{
              padding: "8px 18px",
              backgroundColor: isPlaying ? "var(--status-warning)" : "var(--brand-primary)",
              border: "none",
              borderRadius: "var(--radius-sm)",
              color: "#ffffff",
              fontWeight: 700,
              cursor: "pointer",
              fontSize: "0.875rem",
            }}
          >
            {isPlaying ? "Pause" : "Play"}
          </button>
          <button
            onClick={handleNext}
            disabled={currentStep >= totalSteps - 1}
            style={{
              padding: "8px 14px",
              backgroundColor: "var(--bg-tertiary)",
              border: "1px solid var(--border-muted)",
              borderRadius: "var(--radius-sm)",
              color: "var(--text-primary)",
              cursor: currentStep >= totalSteps - 1 ? "not-allowed" : "pointer",
              opacity: currentStep >= totalSteps - 1 ? 0.5 : 1,
              fontSize: "0.875rem",
            }}
          >
            Next &gt;
          </button>
        </div>

        {/* Speed Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Speed:</span>
          {[0.5, 1, 2, 4].map((spd) => (
            <button
              key={`spd-${spd}`}
              onClick={() => setSpeedMultiplier(spd)}
              style={{
                padding: "4px 8px",
                fontSize: "0.75rem",
                borderRadius: "var(--radius-sm)",
                backgroundColor: speedMultiplier === spd ? "var(--brand-primary)" : "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                color: speedMultiplier === spd ? "#ffffff" : "var(--text-secondary)",
                cursor: "pointer",
              }}
            >
              {spd}x
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
