/**
 * TypeScript types for Phase 8 Interview Simulation System.
 */

export type InterviewMode =
  | 'MOCK_TECHNICAL'
  | 'SYSTEM_DESIGN'
  | 'BEHAVIORAL'
  | 'SPEED_DSA'
  | 'COMPANY_FAANG'
  | 'COMPANY_STARTUP'
  | 'PAIR_PROGRAMMING';

export type InterviewStatus =
  | 'SCHEDULED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'ABANDONED'
  | 'EXPIRED';

export interface InterviewQuestionItem {
  id: string;
  sequence: number;
  title: string;
  problem_id?: string | null;
  question_text: string;
  category: string;
  difficulty: string;
  expected_topics?: string[] | null;
  time_limit_minutes: number;
  is_answered: boolean;
  user_response?: string | null;
  code_language?: string | null;
  score?: number | null;
  feedback?: string | null;
}

export interface InterviewSessionSummary {
  id: string;
  mode: InterviewMode;
  target_company?: string | null;
  target_role?: string | null;
  difficulty: string;
  status: InterviewStatus;
  duration_minutes: number;
  total_questions: number;
  answered_questions: number;
  overall_score?: number | null;
  verdict?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
  created_at: string;
}

export interface InterviewSessionDetail extends InterviewSessionSummary {
  remaining_seconds: number;
  questions: InterviewQuestionItem[];
  feedback_summary?: string | null;
  rubric_breakdown?: Record<string, number> | null;
  improvement_areas?: string[] | null;
}

export interface StartInterviewPayload {
  mode: InterviewMode;
  target_company?: string;
  target_role?: string;
  difficulty?: string;
  duration_minutes?: number;
}

export interface SubmitAnswerPayload {
  user_response: string;
  code_language?: string;
}

export interface InterviewEvaluationReport {
  session_id: string;
  mode: InterviewMode;
  overall_score: number;
  verdict: string;
  rubric_breakdown: Record<string, number>;
  feedback_summary: string;
  strengths: string[];
  improvement_areas: string[];
  recommended_problems: Array<{
    problem_id: string;
    title: string;
    difficulty: string;
  }>;
}
