import React, { useEffect, useState } from "react";
import { oopApi } from "../services/oopApi.ts";
import { OOPOverview } from "../types/oop.ts";

interface OopPageProps {
  onNavigate: (path: string) => void;
}

export const OopPage: React.FC<OopPageProps> = () => {
  const [activeTab, setActiveTab] = useState<"PILLARS" | "SOLID" | "PATTERNS">("PILLARS");
  const [overview, setOverview] = useState<OOPOverview | null>(null);
  const [selectedLang, setSelectedLang] = useState<string>("python");
  const [selectedPillarId, setSelectedPillarId] = useState<string>("encapsulation");
  const [selectedSolidLetter, setSelectedSolidLetter] = useState<string>("S");
  const [selectedPatternName, setSelectedPatternName] = useState<string>("Factory Method");
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchOverview = async () => {
      setLoading(true);
      try {
        const data = await oopApi.getOverview();
        setOverview(data);
      } catch (err: unknown) {
        setErrorMsg(err instanceof Error ? err.message : "Failed to load OOP modules");
      } finally {
        setLoading(false);
      }
    };
    fetchOverview();
  }, []);

  if (loading) {
    return (
      <div style={{ maxWidth: 1100, margin: "60px auto", textAlign: "center", color: "#64748b" }}>
        Loading Object-Oriented Design & Pattern Guide...
      </div>
    );
  }

  if (errorMsg || !overview) {
    return (
      <div style={{ maxWidth: 700, margin: "60px auto", padding: 24, textAlign: "center" }}>
        <h2>OOP Module Unavailable</h2>
        <p style={{ color: "#dc2626" }}>{errorMsg || "Unable to display OOP contents."}</p>
      </div>
    );
  }

  const activePillar = overview.pillars.find((p) => p.id === selectedPillarId) || overview.pillars[0];
  const activeSolid = overview.solid_principles.find((s) => s.letter === selectedSolidLetter) || overview.solid_principles[0];
  const activePattern = overview.design_patterns.find((dp) => dp.name === selectedPatternName) || overview.design_patterns[0];

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "32px 20px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 32, flexWrap: "wrap", gap: 16 }}>
        <div>
          <h1 style={{ margin: "0 0 8px 0", fontSize: 28, fontWeight: 700, color: "#0f172a" }}>
            🏛️ Object-Oriented Design & SOLID Patterns
          </h1>
          <p style={{ margin: 0, color: "#64748b", fontSize: 16 }}>
            Master clean code principles, SOLID design, and Gang-of-Four architectural patterns with multi-language implementations.
          </p>
        </div>

        {/* Global Language Selector */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: "#475569" }}>Code Language:</label>
          <select
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
            style={{
              padding: "6px 12px",
              borderRadius: 6,
              border: "1px solid #cbd5e1",
              backgroundColor: "#fff",
              fontSize: 13,
            }}
          >
            <option value="python">Python</option>
            <option value="java">Java</option>
            <option value="cpp">C++</option>
            <option value="typescript">TypeScript</option>
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", borderBottom: "1px solid #e2e8f0", marginBottom: 24, gap: 24 }}>
        <button
          onClick={() => setActiveTab("PILLARS")}
          style={{
            background: "none",
            border: "none",
            padding: "10px 4px",
            fontSize: 15,
            fontWeight: 600,
            cursor: "pointer",
            color: activeTab === "PILLARS" ? "#2563eb" : "#64748b",
            borderBottom: activeTab === "PILLARS" ? "2px solid #2563eb" : "2px solid transparent",
          }}
        >
          Four Pillars of OOP
        </button>
        <button
          onClick={() => setActiveTab("SOLID")}
          style={{
            background: "none",
            border: "none",
            padding: "10px 4px",
            fontSize: 15,
            fontWeight: 600,
            cursor: "pointer",
            color: activeTab === "SOLID" ? "#2563eb" : "#64748b",
            borderBottom: activeTab === "SOLID" ? "2px solid #2563eb" : "2px solid transparent",
          }}
        >
          SOLID Principles
        </button>
        <button
          onClick={() => setActiveTab("PATTERNS")}
          style={{
            background: "none",
            border: "none",
            padding: "10px 4px",
            fontSize: 15,
            fontWeight: 600,
            cursor: "pointer",
            color: activeTab === "PATTERNS" ? "#2563eb" : "#64748b",
            borderBottom: activeTab === "PATTERNS" ? "2px solid #2563eb" : "2px solid transparent",
          }}
        >
          GoF Design Patterns
        </button>
      </div>

      {/* Tab: Pillars */}
      {activeTab === "PILLARS" && (
        <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 24 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {overview.pillars.map((p) => {
              const isSelected = p.id === selectedPillarId;
              return (
                <div
                  key={p.id}
                  onClick={() => setSelectedPillarId(p.id)}
                  style={{
                    padding: "14px 16px",
                    borderRadius: 8,
                    border: isSelected ? "2px solid #2563eb" : "1px solid #e2e8f0",
                    backgroundColor: isSelected ? "#eff6ff" : "#ffffff",
                    cursor: "pointer",
                  }}
                >
                  <div style={{ fontWeight: 600, color: "#0f172a" }}>{p.name}</div>
                  <div style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>{p.summary}</div>
                </div>
              );
            })}
          </div>

          {activePillar && (
            <div style={{ padding: 24, borderRadius: 12, backgroundColor: "#ffffff", border: "1px solid #e2e8f0" }}>
              <h2 style={{ margin: "0 0 12px 0", fontSize: 22, color: "#0f172a" }}>{activePillar.name}</h2>
              <p style={{ color: "#334155", fontSize: 15, lineHeight: 1.6, marginBottom: 20 }}>
                {activePillar.explanation}
              </p>

              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#475569", marginBottom: 8 }}>
                  Code Implementation ({selectedLang.toUpperCase()})
                </div>
                <pre
                  style={{
                    padding: 16,
                    borderRadius: 8,
                    backgroundColor: "#0f172a",
                    color: "#f8fafc",
                    fontFamily: "monospace",
                    fontSize: 14,
                    overflowX: "auto",
                  }}
                >
                  {activePillar.code_examples[selectedLang] || activePillar.code_examples["python"]}
                </pre>
              </div>

              {activePillar.common_pitfalls && (
                <div style={{ padding: 16, borderRadius: 8, backgroundColor: "#fffbeb", border: "1px solid #fde68a" }}>
                  <div style={{ fontWeight: 700, fontSize: 13, color: "#92400e", marginBottom: 6 }}>
                    ⚠️ Common Pitfalls & Anti-Patterns:
                  </div>
                  <ul style={{ margin: 0, paddingLeft: 20, color: "#92400e", fontSize: 13 }}>
                    {activePillar.common_pitfalls.map((pit, idx) => (
                      <li key={idx} style={{ marginBottom: 4 }}>{pit}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab: SOLID */}
      {activeTab === "SOLID" && (
        <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 24 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {overview.solid_principles.map((s) => {
              const isSelected = s.letter === selectedSolidLetter;
              return (
                <div
                  key={s.letter}
                  onClick={() => setSelectedSolidLetter(s.letter)}
                  style={{
                    padding: "14px 16px",
                    borderRadius: 8,
                    border: isSelected ? "2px solid #2563eb" : "1px solid #e2e8f0",
                    backgroundColor: isSelected ? "#eff6ff" : "#ffffff",
                    cursor: "pointer",
                  }}
                >
                  <div style={{ fontWeight: 700, color: "#2563eb", fontSize: 18 }}>{s.letter}</div>
                  <div style={{ fontWeight: 600, color: "#0f172a", fontSize: 14 }}>{s.name}</div>
                </div>
              );
            })}
          </div>

          {activeSolid && (
            <div style={{ padding: 24, borderRadius: 12, backgroundColor: "#ffffff", border: "1px solid #e2e8f0" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
                <span style={{ fontSize: 24, fontWeight: 800, color: "#2563eb" }}>{activeSolid.letter}</span>
                <h2 style={{ margin: 0, fontSize: 22, color: "#0f172a" }}>{activeSolid.name}</h2>
              </div>
              <p style={{ color: "#334155", fontSize: 15, lineHeight: 1.6, marginBottom: 20 }}>
                {activeSolid.summary}
              </p>

              {/* Side by side code diff */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "#dc2626", marginBottom: 6 }}>
                    ❌ Violation (Bad)
                  </div>
                  <pre
                    style={{
                      padding: 14,
                      borderRadius: 8,
                      backgroundColor: "#0f172a",
                      color: "#fca5a5",
                      fontFamily: "monospace",
                      fontSize: 13,
                      overflowX: "auto",
                    }}
                  >
                    {activeSolid.bad_example[selectedLang] || activeSolid.bad_example["python"]}
                  </pre>
                </div>

                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "#16a34a", marginBottom: 6 }}>
                    ✅ Refactored (Good)
                  </div>
                  <pre
                    style={{
                      padding: 14,
                      borderRadius: 8,
                      backgroundColor: "#0f172a",
                      color: "#86efac",
                      fontFamily: "monospace",
                      fontSize: 13,
                      overflowX: "auto",
                    }}
                  >
                    {activeSolid.good_example[selectedLang] || activeSolid.good_example["python"]}
                  </pre>
                </div>
              </div>

              {activeSolid.benefits && (
                <div style={{ padding: 14, borderRadius: 8, backgroundColor: "#f0fdf4", border: "1px solid #bbf7d0" }}>
                  <div style={{ fontWeight: 700, fontSize: 13, color: "#166534", marginBottom: 6 }}>
                    Engineering Benefits:
                  </div>
                  <ul style={{ margin: 0, paddingLeft: 20, color: "#166534", fontSize: 13 }}>
                    {activeSolid.benefits.map((b, idx) => (
                      <li key={idx} style={{ marginBottom: 4 }}>{b}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab: Patterns */}
      {activeTab === "PATTERNS" && (
        <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 24 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {overview.design_patterns.map((dp) => {
              const isSelected = dp.name === selectedPatternName;
              return (
                <div
                  key={dp.name}
                  onClick={() => setSelectedPatternName(dp.name)}
                  style={{
                    padding: "14px 16px",
                    borderRadius: 8,
                    border: isSelected ? "2px solid #2563eb" : "1px solid #e2e8f0",
                    backgroundColor: isSelected ? "#eff6ff" : "#ffffff",
                    cursor: "pointer",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontWeight: 600, color: "#0f172a" }}>{dp.name}</span>
                    <span style={{ fontSize: 10, padding: "1px 6px", borderRadius: 4, backgroundColor: "#f1f5f9", color: "#475569" }}>
                      {dp.category}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {activePattern && (
            <div style={{ padding: 24, borderRadius: 12, backgroundColor: "#ffffff", border: "1px solid #e2e8f0" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                <h2 style={{ margin: 0, fontSize: 22, color: "#0f172a" }}>{activePattern.name}</h2>
                <span style={{ fontSize: 12, padding: "2px 8px", borderRadius: 4, backgroundColor: "#dbeafe", color: "#1d4ed8", fontWeight: 600 }}>
                  {activePattern.category}
                </span>
              </div>
              <p style={{ color: "#334155", fontSize: 15, lineHeight: 1.6, marginBottom: 16 }}>
                <strong>Intent: </strong>{activePattern.intent}
              </p>

              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#475569", marginBottom: 8 }}>
                  Implementation Pattern ({selectedLang.toUpperCase()})
                </div>
                <pre
                  style={{
                    padding: 16,
                    borderRadius: 8,
                    backgroundColor: "#0f172a",
                    color: "#f8fafc",
                    fontFamily: "monospace",
                    fontSize: 14,
                    overflowX: "auto",
                  }}
                >
                  {activePattern.implementation[selectedLang] || activePattern.implementation["python"]}
                </pre>
              </div>

              {activePattern.use_cases && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 700, fontSize: 13, color: "#1e293b", marginBottom: 6 }}>
                    Real-World Use Cases:
                  </div>
                  <ul style={{ margin: 0, paddingLeft: 20, color: "#475569", fontSize: 13 }}>
                    {activePattern.use_cases.map((uc, idx) => (
                      <li key={idx} style={{ marginBottom: 4 }}>{uc}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
