/**
 * Frontend API client for Phase 8 Mock Interview System.
 */

import { fetchApi } from "./apiClient.ts";
import {
  InterviewSessionSummary,
  InterviewSessionDetail,
  StartInterviewPayload,
  SubmitAnswerPayload,
  InterviewEvaluationReport,
} from "../types/interview.ts";

export const interviewApi = {
  async getSessions(): Promise<InterviewSessionSummary[]> {
    const res = await fetchApi<InterviewSessionSummary[]>("/api/v1/interview/sessions");
    return res.data || [];
  },

  async startInterview(payload: StartInterviewPayload): Promise<InterviewSessionDetail> {
    const res = await fetchApi<InterviewSessionDetail>("/api/v1/interview/start", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (!res.data) throw new Error("Failed to start interview");
    return res.data;
  },

  async getSessionDetail(sessionId: string): Promise<InterviewSessionDetail> {
    const res = await fetchApi<InterviewSessionDetail>(
      `/api/v1/interview/sessions/${sessionId}`
    );
    if (!res.data) throw new Error("Session not found");
    return res.data;
  },

  async submitAnswer(
    sessionId: string,
    questionId: string,
    payload: SubmitAnswerPayload
  ): Promise<{ message: string; score?: number; feedback?: string }> {
    const res = await fetchApi<{ message: string; score?: number; feedback?: string }>(
      `/api/v1/interview/sessions/${sessionId}/questions/${questionId}/answer`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
    return res.data || { message: "Answer submitted" };
  },

  async endSession(sessionId: string): Promise<InterviewEvaluationReport> {
    const res = await fetchApi<InterviewEvaluationReport>(
      `/api/v1/interview/sessions/${sessionId}/end`,
      { method: "POST" }
    );
    if (!res.data) throw new Error("Failed to finalize session");
    return res.data;
  },

  async getReport(sessionId: string): Promise<InterviewEvaluationReport> {
    const res = await fetchApi<InterviewEvaluationReport>(
      `/api/v1/interview/sessions/${sessionId}/report`
    );
    if (!res.data) throw new Error("Report not found");
    return res.data;
  },
};
