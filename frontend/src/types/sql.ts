/**
 * TypeScript types for Phase 8 Interactive SQL Learning Engine.
 */

export interface SQLTableColumn {
  name: string;
  type: string;
  is_pk?: boolean;
}

export interface SQLTableSchema {
  table_name: string;
  columns: SQLTableColumn[];
  sample_rows?: Array<Record<string, unknown>>;
}

export interface SQLProblemSummary {
  id: string;
  title: string;
  slug: string;
  category: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD';
  concepts: string[];
  solved_count: number;
  is_solved: boolean;
}

export interface SQLProblemDetail extends SQLProblemSummary {
  description: string;
  schema_ddl: string;
  seed_sql: string;
  parsed_schemas: SQLTableSchema[];
  hints: string[];
}

export interface SQLQueryResult {
  columns: string[];
  rows: Array<Array<unknown>>;
  row_count: number;
  execution_time_ms: number;
}

export interface SQLSubmissionPayload {
  query: string;
}

export interface SQLSubmissionResult {
  is_correct: boolean;
  verdict: 'ACCEPTED' | 'WRONG_ANSWER' | 'SYNTAX_ERROR' | 'SECURITY_VIOLATION' | 'TIMEOUT';
  error_message?: string | null;
  user_result?: SQLQueryResult | null;
  expected_result?: SQLQueryResult | null;
  execution_time_ms: number;
  xp_awarded: number;
  streak_updated: boolean;
}
