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
    const res: any = await fetchApi<any>(`/api/v1/sql/problems${q}`);
    if (Array.isArray(res)) return res;
    if (Array.isArray(res?.data)) return res.data;
    return [];
  },

  async getProblemDetail(slug: string): Promise<SQLProblemDetail> {
    const res: any = await fetchApi<any>(`/api/v1/sql/problems/${slug}`);
    const data = res?.data ?? res;
    if (!data || (!data.title && !data.id)) throw new Error("SQL problem not found");
    return data;
  },

  async submitQuery(
    slug: string,
    payload: SQLSubmissionPayload
  ): Promise<SQLSubmissionResult> {
    const res: any = await fetchApi<any>(
      `/api/v1/sql/problems/${slug}/submit`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
    const data = res?.data ?? res;
    if (!data) throw new Error("Query submission failed");
    return data;
  },
};
