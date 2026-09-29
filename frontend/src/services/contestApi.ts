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
    const res = await fetchApi<ContestSummary[]>(`/api/v1/contests${q}`);
    return res.data || [];
  },

  async getContestDetail(slug: string): Promise<ContestDetail> {
    const res = await fetchApi<ContestDetail>(`/api/v1/contests/${slug}`);
    if (!res.data) throw new Error("Contest not found");
    return res.data;
  },

  async registerForContest(slug: string): Promise<{ success: boolean; message: string }> {
    const res = await fetchApi<{ success: boolean; message: string }>(
      `/api/v1/contests/${slug}/join`,
      { method: "POST" }
    );
    return res.data || { success: false, message: "Registration failed" };
  },

  async submitSolution(
    slug: string,
    payload: ContestSubmitPayload
  ): Promise<ContestSubmitResult> {
    const res = await fetchApi<ContestSubmitResult>(
      `/api/v1/contests/${slug}/submit`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
    if (!res.data) throw new Error("Submission failed");
    return res.data;
  },

  async getLeaderboard(slug: string): Promise<ContestLeaderboard> {
    const res = await fetchApi<ContestLeaderboard>(
      `/api/v1/contests/${slug}/leaderboard`
    );
    if (!res.data) throw new Error("Leaderboard unavailable");
    return res.data;
  },

  async getMyContestHistory(): Promise<UserContestHistory[]> {
    const res = await fetchApi<UserContestHistory[]>(
      "/api/v1/contests/my-history"
    );
    return res.data || [];
  },
};
