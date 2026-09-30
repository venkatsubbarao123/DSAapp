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
    const res = await fetchApi<any>("/api/v1/interview/sessions");
    const list = res.data || res;
    return Array.isArray(list) ? list : [];
  },

  async startInterview(payload: StartInterviewPayload): Promise<InterviewSessionDetail> {
    const res = await fetchApi<any>("/api/v1/interview/start", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const session = res.data || res;
    if (!session || !session.id) throw new Error("Failed to start interview");
    return session;
  },

  async getSessionDetail(sessionId: string): Promise<InterviewSessionDetail> {
    const res = await fetchApi<any>(
      `/api/v1/interview/sessions/${sessionId}`
    );
    const session = res.data || res;
    if (!session || !session.id) throw new Error("Session not found");
    return session;
  },

  async submitAnswer(
    sessionId: string,
    questionId: string,
    payload: SubmitAnswerPayload
  ): Promise<{ message: string; score?: number; feedback?: string }> {
    const res = await fetchApi<any>(
      `/api/v1/interview/sessions/${sessionId}/questions/${questionId}/answer`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
    return res.data || res || { message: "Answer submitted" };
  },

  async endSession(sessionId: string): Promise<InterviewEvaluationReport> {
    const res = await fetchApi<any>(
      `/api/v1/interview/sessions/${sessionId}/end`,
      { method: "POST" }
    );
    const report = res.data || res;
    if (!report) throw new Error("Failed to finalize session");
    return report;
  },

  async getReport(sessionId: string): Promise<InterviewEvaluationReport> {
    const res = await fetchApi<any>(
      `/api/v1/interview/sessions/${sessionId}/report`
    );
    const report = res.data || res;
    if (!report) throw new Error("Report not found");
    return report;
  },
};
