import React, { useEffect, useState, useRef } from "react";
import { interviewApi } from "../services/interviewApi.ts";
import {
  InterviewSessionDetail,
  InterviewQuestionItem,
} from "../types/interview.ts";

interface InterviewSessionPageProps {
  sessionId: string;
  onNavigate: (path: string) => void;
}

export const InterviewSessionPage: React.FC<InterviewSessionPageProps> = ({
  sessionId,
  onNavigate,
}) => {
  const [session, setSession] = useState<InterviewSessionDetail | null>(null);
  const [currentIdx, setCurrentIdx] = useState<number>(0);
  const [userResponse, setUserResponse] = useState<string>("");
  const [codeLanguage, setCodeLanguage] = useState<string>("python");
  const [remainingSec, setRemainingSec] = useState<number>(0);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [ending, setEnding] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadSession = async () => {
    try {
      const data = await interviewApi.getSessionDetail(sessionId);
      setSession(data);
      setRemainingSec(data.remaining_seconds);
      if (data.status === "COMPLETED") {
        onNavigate(`/interview/${sessionId}/report`);
      }
      if (data.questions && data.questions.length > 0) {
        setUserResponse(data.questions[currentIdx]?.user_response || "");
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to load session");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSession();
  }, [sessionId]);

  // Local ticker for interview countdown
  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setRemainingSec((prev) => {
        if (prev <= 1) {
          handleEndSession();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [session?.status]);

  const currentQuestion: InterviewQuestionItem | undefined = session?.questions[currentIdx];

  const handleSaveAnswer = async () => {
    if (!currentQuestion) return;
    setSubmitting(true);
    setActionNotice(null);
    try {
      const res = await interviewApi.submitAnswer(sessionId, currentQuestion.id, {
        user_response: userResponse,
        code_language: codeLanguage,
      });
      setActionNotice(res.message);
      // Refresh session
      await loadSession();
    } catch (err: unknown) {
      setActionNotice(err instanceof Error ? err.message : "Failed to record response");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEndSession = async () => {
    setEnding(true);
    try {
      await interviewApi.endSession(sessionId);
      onNavigate(`/interview/${sessionId}/report`);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to complete interview");
      setEnding(false);
    }
  };

  const formatCountdown = (seconds: number) => {
    if (seconds <= 0) return "00:00:00";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  if (loading) {
    return (
      <div style={{ maxWidth: 1000, margin: "60px auto", textAlign: "center" }}>
        Connecting to Interview Simulator...
      </div>
    );
  }

  if (errorMsg || !session) {
    return (
      <div style={{ maxWidth: 700, margin: "60px auto", padding: 24, textAlign: "center" }}>
        <h2>Session Unavailable</h2>
        <p style={{ color: "#dc2626" }}>{errorMsg || "Unable to join session."}</p>
        <button
          onClick={() => onNavigate("/interview")}
          style={{
            padding: "8px 16px",
            backgroundColor: "#2563eb",
            color: "#fff",
            borderRadius: 6,
            border: "none",
            cursor: "pointer",
          }}
        >
          Return to Interviews
        </button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "24px 20px" }}>
      {/* Session Top Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "16px 20px",
          borderRadius: 12,
          backgroundColor: "#ffffff",
          border: "1px solid #e2e8f0",
          marginBottom: 24,
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span
              style={{
                fontSize: 12,
                fontWeight: 700,
                padding: "2px 8px",
                borderRadius: 4,
                backgroundColor: "#dbeafe",
                color: "#1d4ed8",
              }}
            >
              {session.mode.replace("_", " ")}
            </span>
            <span style={{ fontSize: 14, color: "#64748b" }}>
              Target: <strong>{session.target_company || "Standard"}</strong> ({session.difficulty})
            </span>
          </div>
          <div style={{ fontSize: 13, color: "#64748b", marginTop: 4 }}>
            Question {currentIdx + 1} of {session.questions.length}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b" }}>SESSION TIMER</div>
            <div
              style={{
                fontSize: 22,
                fontWeight: 800,
                fontFamily: "monospace",
                color: remainingSec < 300 ? "#dc2626" : "#0f172a",
              }}
            >
              {formatCountdown(remainingSec)}
            </div>
          </div>

          <button
            onClick={handleEndSession}
            disabled={ending}
            style={{
              padding: "8px 16px",
              borderRadius: 6,
              backgroundColor: "#ef4444",
              color: "#ffffff",
              fontSize: 13,
              fontWeight: 600,
              border: "none",
              cursor: "pointer",
            }}
          >
            {ending ? "Grading..." : "Finish Interview"}
          </button>
        </div>
      </div>

      {actionNotice && (
        <div
          style={{
            padding: 12,
            marginBottom: 20,
            borderRadius: 8,
            backgroundColor: "#ecfdf5",
            color: "#065f46",
            border: "1px solid #a7f3d0",
          }}
        >
          ✓ {actionNotice}
        </div>
      )}

      {/* Main Workspace Layout */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        {/* Left Panel: Question Prompt & Hints */}
        <div
          style={{
            backgroundColor: "#ffffff",
            padding: 24,
            borderRadius: 12,
            border: "1px solid #e2e8f0",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div>
            <h2 style={{ margin: "0 0 12px 0", fontSize: 20, color: "#0f172a" }}>
              {currentQuestion?.title || `Question ${currentIdx + 1}`}
            </h2>
            <div
              style={{
                padding: 16,
                borderRadius: 8,
                backgroundColor: "#f8fafc",
                border: "1px solid #e2e8f0",
                fontSize: 15,
                lineHeight: 1.6,
                color: "#1e293b",
                whiteSpace: "pre-wrap",
                marginBottom: 20,
              }}
            >
              {currentQuestion?.question_text}
            </div>

            {currentQuestion?.expected_topics && (
              <div style={{ marginTop: 12 }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: "#64748b" }}>Topics Evaluated: </span>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 4 }}>
                  {currentQuestion.expected_topics.map((t) => (
                    <span
                      key={t}
                      style={{
                        fontSize: 11,
                        padding: "2px 8px",
                        borderRadius: 4,
                        backgroundColor: "#f1f5f9",
                        color: "#475569",
                      }}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Question Navigation */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              borderTop: "1px solid #e2e8f0",
              paddingTop: 16,
              marginTop: 20,
            }}
          >
            <button
              onClick={() => {
                if (currentIdx > 0) {
                  setCurrentIdx(currentIdx - 1);
                  setUserResponse(session.questions[currentIdx - 1]?.user_response || "");
                }
              }}
              disabled={currentIdx === 0}
              style={{
                padding: "6px 14px",
                borderRadius: 6,
                border: "1px solid #cbd5e1",
                backgroundColor: "#fff",
                cursor: currentIdx === 0 ? "not-allowed" : "pointer",
                color: currentIdx === 0 ? "#94a3b8" : "#334155",
              }}
            >
              ← Previous
            </button>

            <span style={{ fontSize: 13, color: "#64748b" }}>
              {currentIdx + 1} of {session.questions.length}
            </span>

            <button
              onClick={() => {
                if (currentIdx < session.questions.length - 1) {
                  setCurrentIdx(currentIdx + 1);
                  setUserResponse(session.questions[currentIdx + 1]?.user_response || "");
                }
              }}
              disabled={currentIdx === session.questions.length - 1}
              style={{
                padding: "6px 14px",
                borderRadius: 6,
                border: "1px solid #cbd5e1",
                backgroundColor: "#fff",
                cursor: currentIdx === session.questions.length - 1 ? "not-allowed" : "pointer",
                color: currentIdx === session.questions.length - 1 ? "#94a3b8" : "#334155",
              }}
            >
              Next →
            </button>
          </div>
        </div>

        {/* Right Panel: Student Answer / Code Editor */}
        <div
          style={{
            backgroundColor: "#ffffff",
            padding: 24,
            borderRadius: 12,
            border: "1px solid #e2e8f0",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <label style={{ fontSize: 14, fontWeight: 600, color: "#1e293b" }}>
              Your Solution & Explanation:
            </label>
            <select
              value={codeLanguage}
              onChange={(e) => setCodeLanguage(e.target.value)}
              style={{
                padding: "4px 8px",
                borderRadius: 6,
                border: "1px solid #cbd5e1",
                fontSize: 12,
              }}
            >
              <option value="python">Python</option>
              <option value="cpp">C++</option>
              <option value="java">Java</option>
              <option value="typescript">TypeScript</option>
              <option value="pseudocode">Pseudocode / Text</option>
            </select>
          </div>

          <textarea
            value={userResponse}
            onChange={(e) => setUserResponse(e.target.value)}
            placeholder="Type your thought process, algorithmic approach, time/space complexity, and code implementation here..."
            rows={18}
            style={{
              flex: 1,
              width: "100%",
              boxSizing: "border-box",
              fontFamily: "monospace",
              fontSize: 14,
              padding: 12,
              borderRadius: 8,
              border: "1px solid #cbd5e1",
              backgroundColor: "#0f172a",
              color: "#f8fafc",
              resize: "none",
              marginBottom: 16,
            }}
          />

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 12, color: "#64748b" }}>
              💡 Answers are scored on correctness, optimality, and clarity.
            </span>
            <button
              onClick={handleSaveAnswer}
              disabled={submitting}
              style={{
                padding: "8px 20px",
                borderRadius: 6,
                backgroundColor: "#2563eb",
                color: "#ffffff",
                fontWeight: 600,
                border: "none",
                cursor: submitting ? "wait" : "pointer",
              }}
            >
              {submitting ? "Saving..." : "Save Response ✓"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
