export interface TutorResponseData {
  explanation: string;
  key_idea: string;
  example?: string;
  next_step?: string;
  related_concept?: string;
  visualization_suggestion?: {
    visualizer_type: string;
    title: string;
    description: string;
    initial_data?: Record<string, any>;
  };
  conversation_id?: string;
}

export interface HintResponseData {
  problem_id: string;
  problem_title: string;
  hint_level: number;
  max_level: number;
  title: string;
  hint_content: string;
  thought_question: string;
  is_last_hint: boolean;
}

export interface ExplainResponseData {
  target_type: string;
  explanation: string;
  breakdown_points: string[];
  key_takeaways: string[];
  code_review_points?: string[];
  suggested_fix?: string;
}

export interface ComplexityResponseData {
  time_complexity: string;
  space_complexity: string;
  best_case: string;
  average_case: string;
  worst_case: string;
  reasoning: string;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  caveats: string[];
}

export interface PatternResponseData {
  primary_pattern: string;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  detected_patterns: string[];
  evidence: Array<{ indicator: string; relevance: string }>;
  alternative_patterns: string[];
  explanation: string;
}

export interface RecommendationResponseData {
  has_sufficient_data: boolean;
  summary_insight: string;
  recommendations: Array<{
    topic_id: string;
    topic_title: string;
    problem_id: string;
    problem_title: string;
    difficulty: string;
    reason: string;
    priority: "HIGH" | "MEDIUM" | "LOW";
    estimated_effort_minutes: number;
  }>;
  weak_topics: Array<{
    topic_id: string;
    topic_title: string;
    mistake_count: number;
    unsolved_attempts: number;
    suggested_action: string;
  }>;
  pending_revisions_count: number;
}

export interface AIUsageSummaryData {
  daily_quota: number;
  daily_used: number;
  daily_remaining: number;
  is_premium: boolean;
  provider: string;
  model: string;
  can_request: boolean;
}
