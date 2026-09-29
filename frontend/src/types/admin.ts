/**
 * Admin, Analytics, Diagnostics, and Audit log TypeScript definitions
 */

export type UserRole = 'STUDENT' | 'CONTENT_EDITOR' | 'MODERATOR' | 'ADMIN';
export type ProblemDifficulty = 'EASY' | 'MEDIUM' | 'HARD' | 'EXPERT';
export type ContentAccessLevel = 'FREE' | 'PREMIUM';
export type ContentStatus = 'DRAFT' | 'REVIEW' | 'PUBLISHED' | 'ARCHIVED';

// --- User Management ---

export interface AdminUserListItem {
  id: string;
  email: string;
  display_name: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  plan: string;
  premium_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminUserListResponse {
  items: AdminUserListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminUserDetail {
  id: string;
  email: string;
  display_name: string;
  bio?: string | null;
  avatar_url?: string | null;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  plan: string;
  premium_active: boolean;
  premium_expires_at?: string | null;
  created_at: string;
  updated_at: string;
  submissions_count: number;
  solved_problems_count: number;
  current_streak: number;
  total_xp: number;
}

export interface AdminUpdateUserRoleRequest {
  role: UserRole;
  reason?: string;
}

export interface AdminUpdateUserStatusRequest {
  is_active: boolean;
  reason?: string;
}

// --- Problems & Test Cases ---

export interface AdminTestCaseItem {
  id: string;
  problem_id: string;
  input: string;
  expected_output: string;
  is_sample: boolean;
  is_hidden: boolean;
  display_order: number;
  created_at: string;
}

export interface AdminCreateTestCaseRequest {
  input: string;
  expected_output: string;
  is_sample?: boolean;
  is_hidden?: boolean;
  display_order?: number;
}

export interface AdminUpdateTestCaseRequest {
  input?: string;
  expected_output?: string;
  is_sample?: boolean;
  is_hidden?: boolean;
  display_order?: number;
}

export interface AdminProblemListItem {
  id: string;
  public_id: string;
  slug: string;
  title: string;
  difficulty: ProblemDifficulty;
  access_level: ContentAccessLevel;
  status: ContentStatus;
  time_limit_ms: number;
  memory_limit_mb: number;
  test_cases_count: number;
  hidden_test_cases_count: number;
  created_at: string;
  updated_at: string;
}

export interface AdminProblemListResponse {
  items: AdminProblemListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// --- System Diagnostics ---

export interface ServiceHealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  message?: string | null;
  latency_ms?: number | null;
  details?: Record<string, any> | null;
}

export interface SystemDiagnosticsResponse {
  app_name: string;
  app_version: string;
  environment: string;
  server_time: string;
  uptime_seconds: number;
  database: ServiceHealthStatus;
  redis: ServiceHealthStatus;
  docker_sandbox: ServiceHealthStatus;
  judge_queue: ServiceHealthStatus;
  ai_provider: ServiceHealthStatus;
  current_migration_revision?: string | null;
}

// --- Audit Trail ---

export interface AuditLogItem {
  id: string;
  actor_id?: string | null;
  action: string;
  target_type?: string | null;
  target_id?: string | null;
  ip_address?: string | null;
  request_id?: string | null;
  metadata_json?: string | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// --- Analytics ---

export interface CategoryCount {
  category: string;
  count: number;
  percentage?: number | null;
}

export interface TimeSeriesPoint {
  date: string;
  count: number;
}

export interface PlatformOverviewMetrics {
  total_users: number;
  active_users_dau: number;
  active_users_wau: number;
  active_users_mau: number;
  total_problems: number;
  total_submissions: number;
  total_accepted_submissions: number;
  platform_acceptance_rate: number;
  total_premium_subscribers: number;
  total_revenue_amount: number;
  currency: string;
}

export interface ProblemStatItem {
  problem_id: string;
  title: string;
  difficulty: string;
  total_attempts: number;
  accepted_attempts: number;
  pass_rate: number;
}

export interface ComprehensiveAnalyticsResponse {
  timestamp: string;
  cached: boolean;
  overview: PlatformOverviewMetrics;
  users: {
    total_users: number;
    active_users: number;
    suspended_users: number;
    verified_users: number;
    role_distribution: CategoryCount[];
    plan_distribution: CategoryCount[];
    signups_last_30_days: TimeSeriesPoint[];
  };
  content: {
    total_problems: number;
    problems_by_difficulty: CategoryCount[];
    problems_by_access_level: CategoryCount[];
    total_submissions: number;
    verdict_distribution: CategoryCount[];
    top_attempted_problems: ProblemStatItem[];
    hardest_problems: ProblemStatItem[];
    submissions_last_30_days: TimeSeriesPoint[];
  };
  gamification: {
    total_xp_distributed: number;
    users_with_active_streaks: number;
    longest_streak_record: number;
    total_badges_unlocked: number;
    streak_tier_distribution: CategoryCount[];
  };
  competition: {
    total_contests: number;
    total_contest_registrations: number;
    total_contest_submissions: number;
    total_mock_interviews: number;
    average_interview_score: number;
    total_sql_submissions: number;
  };
  judge: {
    queue_depth: number;
    running_jobs: number;
    total_jobs_executed: number;
    sandbox_status: string;
    verdict_breakdown: CategoryCount[];
    supported_languages: string[];
  };
  revenue: {
    total_orders: number;
    successful_orders: number;
    failed_orders: number;
    total_revenue: number;
    currency: string;
    active_subscriptions: number;
    revenue_last_30_days: any[];
  };
}
