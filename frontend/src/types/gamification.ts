/**
 * Frontend domain types for Phase 7 Practice Engine & Gamification.
 */

export type PracticeMode =
  | "QUICK"
  | "TOPIC"
  | "PATTERN"
  | "DIFFICULTY"
  | "WEAK_AREA"
  | "MISTAKES"
  | "REVISION"
  | "DAILY_CHALLENGE";

export type PracticeSessionStatus = "IN_PROGRESS" | "COMPLETED" | "ABANDONED";

export interface PracticeSessionProblem {
  id: string;
  session_id: string;
  problem_id: string;
  sequence: number;
  served_at: string;
  attempted: boolean;
  solved: boolean;
  submission_id?: string | null;
  time_spent_seconds: number;
  problem_title: string;
  problem_slug: string;
  difficulty: string;
}

export interface PracticeSession {
  id: string;
  user_id: string;
  mode: PracticeMode;
  topic_id?: string | null;
  topic_title?: string | null;
  pattern_id?: string | null;
  pattern_name?: string | null;
  difficulty?: string | null;
  status: PracticeSessionStatus;
  target_count: number;
  completed_count: number;
  solved_count: number;
  xp_earned: number;
  accuracy: number;
  duration_seconds: number;
  started_at: string;
  completed_at?: string | null;
  problems: PracticeSessionProblem[];
}

export interface UserGamificationProfile {
  user_id: string;
  total_xp: number;
  current_level: number;
  current_level_floor_xp: number;
  next_level_ceiling_xp: number;
  xp_in_current_level: number;
  xp_needed_for_next_level: number;
  level_progress_percent: number;
  current_streak: number;
  longest_streak: number;
  streak_freeze_count: number;
  last_activity_date?: string | null;
  skill_rating: number;
  total_problems_solved: number;
  total_practice_sessions_completed: number;
}

export interface DailyChallengeData {
  id: string;
  challenge_date: string;
  problem_id: string;
  problem_title: string;
  problem_slug: string;
  difficulty: string;
  xp_reward: number;
  bonus_xp: number;
  solved: boolean;
  first_attempt_solve: boolean;
  xp_awarded: number;
  can_claim: boolean;
}

export interface ClaimDailyRewardResponse {
  success: boolean;
  xp_awarded: number;
  message: string;
}

export interface AchievementBadge {
  id: string;
  code: string;
  name: string;
  description: string;
  category: string;
  tier: "BRONZE" | "SILVER" | "GOLD" | "PLATINUM";
  icon_name: string;
  xp_reward: number;
  unlocked: boolean;
  unlocked_at?: string | null;
  progress_value: number;
  target_value: number;
  progress_percent: number;
}

export interface AchievementsResponse {
  total_achievements: number;
  unlocked_count: number;
  achievements: AchievementBadge[];
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  display_name: string;
  score: number;
  current_level: number;
  current_streak: number;
}

export interface LeaderboardResponse {
  category: string;
  period_start?: string | null;
  period_end?: string | null;
  total_participants: number;
  entries: LeaderboardEntry[];
}

export interface ProblemRecommendation {
  problem_id: string;
  slug: string;
  title: string;
  difficulty: string;
  topic_id?: string | null;
  score: number;
  reasons: string[];
  category: string;
}

export interface RecommendationExplanation {
  problem_id: string;
  title: string;
  explanation: string;
  pedagogical_factors: string[];
  metrics: Record<string, unknown>;
}

export interface XPLedgerTransaction {
  id: string;
  event_type: string;
  amount: number;
  balance_after: number;
  source_id?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
}

export interface XPLedgerResponse {
  total_count: number;
  total_xp: number;
  transactions: XPLedgerTransaction[];
}

export interface RatingHistoryEntry {
  id: string;
  change_amount: number;
  new_rating: number;
  reason: string;
  source_id?: string | null;
  created_at: string;
}

export interface RatingHistoryResponse {
  current_rating: number;
  history: RatingHistoryEntry[];
}
