/**
 * Curriculum, Topics, Lessons, and Problem specifications matching Phase 3 backend contracts.
 */

export type ContentLevel = "BEGINNER" | "INTERMEDIATE" | "ADVANCED" | "EXPERT";
export type ContentStatus = "DRAFT" | "REVIEW" | "PUBLISHED" | "ARCHIVED";
export type ContentAccessLevel = "FREE" | "PREMIUM";
export type ProblemDifficulty = "EASY" | "MEDIUM" | "HARD" | "EXPERT";

export interface PaginatedData<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface LessonBlock {
  type: "heading" | "paragraph" | "code" | "note" | "tip" | "warning" | "example" | "table";
  content: string;
  level?: number;
  language?: string;
  metadata?: Record<string, unknown>;
}

export interface Tag {
  id: string;
  slug: string;
  name: string;
}

export interface Pattern {
  id: string;
  slug: string;
  name: string;
  description: string;
}

export interface ProblemExample {
  id: string;
  input: string;
  output: string;
  explanation?: string;
  display_order: number;
}

export interface Hint {
  id: string;
  hint_number: number;
  title: string;
  content: string;
  is_premium: boolean;
}

export interface TestCase {
  id: string;
  input: string;
  expected_output: string;
  is_sample: boolean;
  display_order: number;
}

export interface CurriculumSummary {
  id: string;
  public_id: string;
  slug: string;
  title: string;
  short_description?: string;
  level: ContentLevel;
  status: ContentStatus;
  display_order: number;
  is_free: boolean;
}

export interface TrackSummary {
  id: string;
  curriculum_id: string;
  slug: string;
  title: string;
  description: string;
  level: ContentLevel;
  display_order: number;
  status: ContentStatus;
  access_level: ContentAccessLevel;
}

export interface CurriculumDetail extends CurriculumSummary {
  description: string;
  tracks: TrackSummary[];
  created_at: string;
  updated_at: string;
}

export interface SubtopicSummary {
  id: string;
  topic_id: string;
  slug: string;
  title: string;
  description: string;
  display_order: number;
  difficulty: ContentLevel;
  access_level: ContentAccessLevel;
  status: ContentStatus;
}

export interface TopicSummary {
  id: string;
  public_id: string;
  track_id?: string;
  slug: string;
  title: string;
  description: string;
  display_order: number;
  difficulty: ContentLevel;
  access_level: ContentAccessLevel;
  status: ContentStatus;
}

export interface TopicDetail extends TopicSummary {
  subtopics: SubtopicSummary[];
  created_at: string;
  updated_at: string;
}

export interface LessonSummary {
  id: string;
  public_id: string;
  subtopic_id: string;
  slug: string;
  title: string;
  summary: string;
  estimated_minutes: number;
  difficulty: ContentLevel;
  display_order: number;
  access_level: ContentAccessLevel;
  status: ContentStatus;
  version: number;
}

export interface LessonDetail extends LessonSummary {
  blocks: LessonBlock[];
  created_at: string;
  updated_at: string;
}

export interface ProblemSummary {
  id: string;
  public_id: string;
  slug: string;
  title: string;
  difficulty: ProblemDifficulty;
  access_level: ContentAccessLevel;
  status: ContentStatus;
  topic_id?: string;
  subtopic_id?: string;
  display_order: number;
  estimated_minutes: number;
  tags: Tag[];
  patterns: Pattern[];
}

export interface ProblemDetail extends ProblemSummary {
  statement: string;
  explanation?: string;
  input_format?: string;
  output_format?: string;
  constraints?: string;
  expected_time_complexity?: string;
  expected_space_complexity?: string;
  supported_languages: string[];
  version: number;
  examples: ProblemExample[];
  hints: Hint[];
  sample_test_cases: TestCase[];
  created_at: string;
  updated_at: string;
}
