/**
 * Frontend API client for Phase 8 Contests.
 */

import { fetchApi } from "./apiClient.ts";
import {
  ContestSummary,
  ContestDetail,
  ContestSubmitPayload,
  ContestSubmitResult,
  ContestLeaderboard,
  UserContestHistory,
} from "../types/contest.ts";

export const contestApi = {
  async getContests(status?: string): Promise<ContestSummary[]> {
    const q = status ? `?status=${status}` : "";
    const res = await fetchApi<any>(`/api/v1/contests${q}`);
    const raw = res as any;
    if (Array.isArray(raw)) return raw;
    return raw?.data || [];
  },

  async getContestDetail(slug: string): Promise<ContestDetail> {
    const res = await fetchApi<any>(`/api/v1/contests/${slug}`);
    const raw = res as any;
    if (raw?.id && raw?.slug) return raw as ContestDetail;
    if (raw?.data) return raw.data as ContestDetail;
    throw new Error("Contest not found");
  },

  async registerForContest(slug: string): Promise<{ success: boolean; message: string }> {
    const res = await fetchApi<any>(
      `/api/v1/contests/${slug}/join`,
      { method: "POST" }
    );
    const raw = res as any;
    if (raw?.success !== undefined) return raw;
    return raw?.data || { success: false, message: "Registration failed" };
  },

  async submitSolution(
    slug: string,
    payload: ContestSubmitPayload
  ): Promise<ContestSubmitResult> {
    const res = await fetchApi<any>(
      `/api/v1/contests/${slug}/submit`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
    const raw = res as any;
    if (raw?.verdict !== undefined) return raw as ContestSubmitResult;
    if (raw?.data) return raw.data as ContestSubmitResult;
    throw new Error("Submission failed");
  },

  async getLeaderboard(slug: string): Promise<ContestLeaderboard> {
    const res = await fetchApi<any>(
      `/api/v1/contests/${slug}/leaderboard`
    );
    const raw = res as any;
    if (raw?.entries || raw?.contest_title) return raw as ContestLeaderboard;
    if (raw?.data) return raw.data as ContestLeaderboard;
    throw new Error("Leaderboard unavailable");
  },

  async getMyContestHistory(): Promise<UserContestHistory[]> {
    const res = await fetchApi<any>(
      "/api/v1/contests/history"
    );
    const raw = res as any;
    if (Array.isArray(raw)) return raw;
    return raw?.data || [];
  },
};
