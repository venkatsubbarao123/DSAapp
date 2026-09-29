/**
 * Frontend API client for Phase 8 Competitive Programming.
 */

import { fetchApi } from "./apiClient.ts";
import {
  CPProblem,
  UserCPRating,
  CPLeaderboardEntry,
  CPRatingBand,
} from "../types/cp.ts";

export const cpApi = {
  async getProblems(params?: { rating_band?: string; tag?: string }): Promise<CPProblem[]> {
    const sp = new URLSearchParams();
    if (params?.rating_band) sp.append("rating_band", params.rating_band);
    if (params?.tag) sp.append("tag", params.tag);
    const query = sp.toString() ? `?${sp.toString()}` : "";
    const res = await fetchApi<CPProblem[]>(`/api/v1/competitive/problems${query}`);
    return res.data || [];
  },

  async getBands(): Promise<CPRatingBand[]> {
    const res = await fetchApi<CPRatingBand[]>("/api/v1/competitive/bands");
    return res.data || [];
  },

  async getMyRating(): Promise<UserCPRating> {
    const res = await fetchApi<UserCPRating>("/api/v1/competitive/rating/me");
    if (!res.data) throw new Error("Rating profile not found");
    return res.data;
  },

  async getLeaderboard(limit = 50): Promise<CPLeaderboardEntry[]> {
    const res = await fetchApi<CPLeaderboardEntry[]>(
      `/api/v1/competitive/leaderboard?limit=${limit}`
    );
    return res.data || [];
  },
};
