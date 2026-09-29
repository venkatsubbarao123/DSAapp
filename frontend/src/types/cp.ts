/**
 * TypeScript types for Phase 8 Competitive Programming System.
 */

export interface CPProblem {
  id: string;
  problem_id: string;
  title: string;
  slug: string;
  rating: number;
  rating_band: string;
  tags: string[];
  cf_contest_id?: number | null;
  cf_index?: string | null;
  platform: string;
  solved_count: number;
  solved_by_user: boolean;
}

export interface CPRatingHistoryEntry {
  contest_id: string;
  contest_title: string;
  rating_before: number;
  rating_after: number;
  rating_change: number;
  rank: number;
  performance_rating?: number | null;
  recorded_at: string;
}

export interface UserCPRating {
  user_id: string;
  current_rating: number;
  max_rating: number;
  contests_attended: number;
  rank_title: string;
  rating_band: string;
  history: CPRatingHistoryEntry[];
}

export interface CPLeaderboardEntry {
  rank: number;
  user_id: string;
  display_name: string;
  current_rating: number;
  max_rating: number;
  contests_attended: number;
  rank_title: string;
}

export interface CPRatingBand {
  name: string;
  min_rating: number;
  max_rating: number;
  color: string;
  problem_count: number;
}
