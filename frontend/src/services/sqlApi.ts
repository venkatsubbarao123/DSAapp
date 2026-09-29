/**
 * Frontend API client for Phase 8 Interactive SQL Learning Engine.
 */

import { fetchApi } from "./apiClient.ts";
import {
  SQLProblemSummary,
  SQLProblemDetail,
  SQLSubmissionPayload,
  SQLSubmissionResult,
} from "../types/sql.ts";

export const sqlApi = {
  async getProblems(category?: string): Promise<SQLProblemSummary[]> {
    const q = category ? `?category=${category}` : "";
    const res = await fetchApi<SQLProblemSummary[]>(`/api/v1/sql/problems${q}`);
    return res.data || [];
  },

  async getProblemDetail(slug: string): Promise<SQLProblemDetail> {
    const res = await fetchApi<SQLProblemDetail>(`/api/v1/sql/problems/${slug}`);
    if (!res.data) throw new Error("SQL problem not found");
    return res.data;
  },

  async submitQuery(
    slug: string,
    payload: SQLSubmissionPayload
  ): Promise<SQLSubmissionResult> {
    const res = await fetchApi<SQLSubmissionResult>(
      `/api/v1/sql/problems/${slug}/submit`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
    if (!res.data) throw new Error("Query submission failed");
    return res.data;
  },
};
