/**
 * TypeScript types for Phase 8 Contest Platform.
 */

export interface ContestSummary {
  id: string;
  title: string;
  slug: string;
  description: string;
  status: 'DRAFT' | 'UPCOMING' | 'LIVE' | 'ENDED' | 'ARCHIVED';
  start_at: string;
  end_at: string;
  duration_seconds: number;
  remaining_seconds: number;
  visibility: string;
  premium_required: boolean;
  participant_count: number;
}

export interface ContestProblem {
  id: string;
  problem_id: string;
  title: string;
  slug: string;
  sequence: number;
  points: number;
  penalty_minutes: number;
  difficulty: string;
  solved: boolean;
  wrong_attempts: number;
}

export interface ContestDetail extends ContestSummary {
  is_registered: boolean;
  my_score: number;
  my_penalty: number;
  my_rank?: number | null;
  problems: ContestProblem[];
}

export interface ContestSubmitPayload {
  problem_id: string;
  language: string;
  source_code: string;
  idempotency_key?: string;
}

export interface ContestSubmitResult {
  submission_id: string;
  contest_submission_id: string;
  verdict: string;
  score: number;
  penalty: number;
  message: string;
}

export interface ProblemResultDetail {
  solved: boolean;
  wrong_attempts: number;
  time_minutes?: number | null;
  points: number;
}

export interface ContestLeaderboardEntry {
  rank: number;
  display_name: string;
  score: number;
  penalty: number;
  problems_solved: number;
  problem_results: Record<string, ProblemResultDetail>;
}

export interface ContestLeaderboard {
  contest_id: string;
  contest_title: string;
  status: string;
  total_participants: number;
  entries: ContestLeaderboardEntry[];
}

export interface UserContestHistory {
  contest_id: string;
  contest_title: string;
  contest_slug: string;
  start_at: string;
  end_at: string;
  joined_at: string;
  final_score: number;
  final_penalty: number;
  final_rank?: number | null;
  total_participants: number;
}
