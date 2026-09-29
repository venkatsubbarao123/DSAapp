/**
 * Typed API client functions for Phase 7 Practice Engine & Gamification.
 */

import { fetchApi } from "./apiClient.ts";
import {
  AchievementsResponse,
  ClaimDailyRewardResponse,
  DailyChallengeData,
  LeaderboardEntry,
  LeaderboardResponse,
  PracticeMode,
  PracticeSession,
  ProblemRecommendation,
  RatingHistoryResponse,
  RecommendationExplanation,
  UserGamificationProfile,
  XPLedgerResponse,
} from "../types/gamification.ts";

export const gamificationApi = {
  // Practice Session Lifecycle
  createPracticeSession: async (
    mode: PracticeMode,
    targetCount: number = 3,
    topicId?: string,
    patternId?: string,
    difficulty?: string
  ): Promise<PracticeSession> => {
    const res = await fetchApi<PracticeSession>("/api/v1/practice/sessions", {
      method: "POST",
      body: JSON.stringify({
        mode,
        target_count: targetCount,
        topic_id: topicId,
        pattern_id: patternId,
        difficulty,
      }),
    });
    return res.data;
  },

  getPracticeSession: async (sessionId: string): Promise<PracticeSession> => {
    const res = await fetchApi<PracticeSession>(`/api/v1/practice/sessions/${sessionId}`);
    return res.data;
  },

  recordProblemResult: async (
    sessionId: string,
    problemId: string,
    solved: boolean,
    timeSpentSeconds: number,
    submissionId?: string
  ): Promise<{ session_id: string; problem_id: string; solved: boolean; xp_awarded: number; accuracy: number }> => {
    const res = await fetchApi<{
      session_id: string;
      problem_id: string;
      solved: boolean;
      xp_awarded: number;
      accuracy: number;
    }>(`/api/v1/practice/sessions/${sessionId}/problem/${problemId}/result`, {
      method: "POST",
      body: JSON.stringify({
        problem_id: problemId,
        solved,
        time_spent_seconds: timeSpentSeconds,
        submission_id: submissionId,
      }),
    });
    return res.data;
  },

  completePracticeSession: async (sessionId: string): Promise<PracticeSession> => {
    const res = await fetchApi<PracticeSession>(`/api/v1/practice/sessions/${sessionId}/complete`, {
      method: "POST",
    });
    return res.data;
  },

  getPracticeHistory: async (limit: number = 10, offset: number = 0): Promise<PracticeSession[]> => {
    const res = await fetchApi<PracticeSession[]>(`/api/v1/practice/history?limit=${limit}&offset=${offset}`);
    return res.data;
  },

  // Recommendations
  getRecommendations: async (mode: PracticeMode = "QUICK", limit: number = 6): Promise<ProblemRecommendation[]> => {
    const res = await fetchApi<ProblemRecommendation[]>(`/api/v1/practice/recommendations?mode=${mode}&limit=${limit}`);
    return res.data;
  },

  explainRecommendation: async (problemId: string): Promise<RecommendationExplanation> => {
    const res = await fetchApi<RecommendationExplanation>(`/api/v1/practice/recommendations/explain/${problemId}`);
    return res.data;
  },

  // Daily Challenge
  getDailyChallenge: async (): Promise<DailyChallengeData> => {
    const res = await fetchApi<DailyChallengeData>("/api/v1/practice/daily");
    return res.data;
  },

  claimDailyReward: async (): Promise<ClaimDailyRewardResponse> => {
    const res = await fetchApi<ClaimDailyRewardResponse>("/api/v1/practice/daily/claim", {
      method: "POST",
    });
    return res.data;
  },

  // Gamification Profile & Metrics
  getUserProfile: async (): Promise<UserGamificationProfile> => {
    const res = await fetchApi<UserGamificationProfile>("/api/v1/gamification/profile");
    return res.data;
  },

  getXPLedger: async (limit: number = 20, offset: number = 0): Promise<XPLedgerResponse> => {
    const res = await fetchApi<XPLedgerResponse>(`/api/v1/gamification/xp?limit=${limit}&offset=${offset}`);
    return res.data;
  },

  getAchievements: async (): Promise<AchievementsResponse> => {
    const res = await fetchApi<AchievementsResponse>("/api/v1/gamification/achievements");
    return res.data;
  },

  getRatingHistory: async (): Promise<RatingHistoryResponse> => {
    const res = await fetchApi<RatingHistoryResponse>("/api/v1/gamification/rating");
    return res.data;
  },

  // Leaderboards
  getLeaderboard: async (
    category: "weekly_xp" | "monthly_xp" | "all_time_xp" | "weekly_solves" | "streak" = "weekly_xp",
    limit: number = 20,
    offset: number = 0
  ): Promise<LeaderboardResponse> => {
    const res = await fetchApi<LeaderboardResponse>(
      `/api/v1/leaderboards?category=${category}&limit=${limit}&offset=${offset}`
    );
    return res.data;
  },

  getUserRank: async (): Promise<Record<string, LeaderboardEntry>> => {
    const res = await fetchApi<Record<string, LeaderboardEntry>>("/api/v1/leaderboards/me");
    return res.data;
  },
};
