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
    const res = await fetchApi<any>(`/api/v1/competitive/problems${query}`);
    const raw = res as any;
    if (Array.isArray(raw)) return raw;
    if (raw && Array.isArray(raw.data)) return raw.data;
    return [];
  },

  async getBands(): Promise<CPRatingBand[]> {
    const res = await fetchApi<any>("/api/v1/competitive/bands");
    const raw = res as any;
    if (Array.isArray(raw)) return raw;
    if (raw && Array.isArray(raw.data)) return raw.data;
    return [];
  },

  async getMyRating(): Promise<UserCPRating> {
    const res = await fetchApi<any>("/api/v1/competitive/profile");
    const raw = res as any;
    if (raw?.current_rating !== undefined) return raw as UserCPRating;
    if (raw?.data?.current_rating !== undefined) return raw.data as UserCPRating;
    if (raw?.data) return raw.data as UserCPRating;
    throw new Error("Rating profile not found");
  },

  async getLeaderboard(limit = 50): Promise<CPLeaderboardEntry[]> {
    const res = await fetchApi<any>(`/api/v1/competitive/leaderboard?limit=${limit}`);
    const raw = res as any;
    if (Array.isArray(raw)) return raw;
    if (raw && Array.isArray(raw.data)) return raw.data;
    if (raw && Array.isArray(raw.entries)) return raw.entries;
    if (raw && raw.data && Array.isArray(raw.data.entries)) return raw.data.entries;
    return [];
  },
};
