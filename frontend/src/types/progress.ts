/**
 * Phase 4 TypeScript definitions for Progress, Submissions, Mistakes, and Spaced Revision.
 */

export type ProblemProgressStatus = "NOT_STARTED" | "ATTEMPTED" | "SOLVED";
export type LessonProgressStatus = "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED";

export type Verdict =
  | "ACCEPTED"
  | "WRONG_ANSWER"
  | "TIME_LIMIT_EXCEEDED"
  | "MEMORY_LIMIT_EXCEEDED"
  | "RUNTIME_ERROR"
  | "COMPILATION_ERROR"
  | "OUTPUT_LIMIT_EXCEEDED"
  | "SYSTEM_ERROR";

export type SubmissionStatus =
  | "CREATED"
  | "QUEUED"
  | "QUEUED_FOR_FUTURE_JUDGE"
  | "NOT_EXECUTED"
  | "RUNNING"
  | "COMPILING"
  | "JUDGING"
  | "ACCEPTED"
  | "WRONG_ANSWER"
  | "TIME_LIMIT_EXCEEDED"
  | "MEMORY_LIMIT_EXCEEDED"
  | "RUNTIME_ERROR"
  | "COMPILATION_ERROR"
  | "OUTPUT_LIMIT_EXCEEDED"
  | "SYSTEM_ERROR"
  | "CANCELLED";

export interface SubmissionResult {
  id: string;
  submission_id: string;
  verdict: Verdict;
  tests_total: number;
  tests_passed: number;
  execution_time_ms?: number | null;
  memory_used_bytes?: number | null;
  compiler_output_safe?: string | null;
  runtime_output_safe?: string | null;
  created_at: string;
}

export interface TestCaseRunResult {
  case_number: number;
  input: string;
  expected_output?: string | null;
  actual_output?: string | null;
  stderr?: string | null;
  passed: boolean;
  execution_time_ms: number;
  status: string;
}

export interface RunCodeResult {
  status: string;
  all_passed: boolean;
  passed_count: number;
  total_count: number;
  peak_runtime_ms: number;
  peak_memory_bytes: number;
  compiler_output?: string | null;
  test_cases: TestCaseRunResult[];
}


export type MistakeType =
  | "CONCEPT_GAP"
  | "LOGIC_ERROR"
  | "EDGE_CASE"
  | "COMPLEXITY_ISSUE"
  | "SYNTAX_ERROR"
  | "IMPLEMENTATION_ERROR"
  | "MISUNDERSTANDING"
  | "OTHER";

export type RevisionSourceType = "LESSON" | "PROBLEM" | "MISTAKE";
export type RevisionScheduleStatus = "ACTIVE" | "COMPLETED" | "PAUSED";
export type ReviewOutcome = "AGAIN" | "HARD" | "GOOD" | "EASY";

export interface ProgressActivityItem {
  title: string;
  entity_type: "LESSON" | "PROBLEM";
  slug: string;
  status: string;
  timestamp: string;
}

export interface ProgressOverview {
  lessons_started: number;
  lessons_completed: number;
  total_visible_lessons: number;
  lesson_completion_percent: number;

  problems_attempted: number;
  problems_solved: number;
  total_visible_problems: number;
  problem_solving_percent: number;

  overall_completion_percent: number;
  recent_activity: ProgressActivityItem[];
  due_revisions_count: number;
  unresolved_mistakes_count: number;
}

export interface TopicProgress {
  topic_id: string;
  topic_title: string;
  topic_slug: string;
  total_lessons: number;
  completed_lessons: number;
  total_problems: number;
  solved_problems: number;
  completion_percent: number;
}

export interface ProblemProgress {
  id: string;
  problem_id: string;
  status: ProblemProgressStatus;
  attempts_count: number;
  successful_attempts: number;
  first_attempted_at?: string;
  last_attempted_at?: string;
  solved_at?: string;
  bookmarked: boolean;
  personal_difficulty?: string;
  created_at: string;
  updated_at: string;
}

export interface MasteryInsights {
  spaced_retention_score: number;
  streak_days: number;
  mistake_breakdown: Record<string, number>;
  pattern_mastery: Array<{ pattern: string; level: string }>;
}

export interface SubmissionSummary {
  id: string;
  public_id: string;
  problem_id: string;
  problem_title: string;
  problem_slug: string;
  language: string;
  status: SubmissionStatus;
  created_at: string;
  execution_notice?: string;
  result?: SubmissionResult | null;
}

export interface SubmissionDetail {
  id: string;
  public_id: string;
  problem_id: string;
  problem_title: string;
  problem_slug: string;
  language: string;
  source_code: string;
  status: SubmissionStatus;
  created_at: string;
  updated_at: string;
  execution_notice?: string;
  result?: SubmissionResult | null;
}

export interface Mistake {
  id: string;
  public_id: string;
  user_id: string;
  problem_id?: string;
  problem_title?: string;
  problem_slug?: string;
  lesson_id?: string;
  lesson_title?: string;
  lesson_slug?: string;
  mistake_type: MistakeType;
  title: string;
  description: string;
  correction?: string;
  is_resolved: boolean;
  resolved_at?: string;
  created_at: string;
  updated_at: string;
}

export interface RevisionSchedule {
  id: string;
  due_at: string;
  last_reviewed_at?: string;
  review_count: number;
  interval_days: number;
  ease_factor: number;
  status: RevisionScheduleStatus;
}

export interface RevisionItem {
  id: string;
  public_id: string;
  source_type: RevisionSourceType;
  source_id: string;
  title: string;
  priority: number;
  is_active: boolean;
  schedule?: RevisionSchedule;
  created_at: string;
  is_overdue: boolean;
  is_due_now: boolean;
}
