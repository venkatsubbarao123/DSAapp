import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AdminLayout } from '../pages/admin/AdminLayout';
import { AdminOverviewPage } from '../pages/admin/AdminOverviewPage';
import { AdminUsersPage } from '../pages/admin/AdminUsersPage';
import { AdminProblemsPage } from '../pages/admin/AdminProblemsPage';
import { AdminSystemPage } from '../pages/admin/AdminSystemPage';
import { AdminAuditPage } from '../pages/admin/AdminAuditPage';
import { AdminBroadcastPage } from '../pages/admin/AdminBroadcastPage';
import { adminApi } from '../services/adminApi';
import { notificationApi } from '../services/notificationApi';
import * as AuthContextModule from '../context/AuthContext';

vi.mock('../services/adminApi', () => ({
  adminApi: {
    getPlatformOverview: vi.fn(),
    getDiagnostics: vi.fn(),
    listUsers: vi.fn(),
    getUser: vi.fn(),
    updateUserRole: vi.fn(),
    updateUserStatus: vi.fn(),
    listProblems: vi.fn(),
    updateProblem: vi.fn(),
    listTestCases: vi.fn(),
    createTestCase: vi.fn(),
    deleteTestCase: vi.fn(),
    getAnalyticsOverview: vi.fn(),
    getUsersAnalytics: vi.fn(),
    getJudgeAnalytics: vi.fn(),
    getRevenueAnalytics: vi.fn(),
    listAuditLogs: vi.fn(),
  },
}));

vi.mock('../services/notificationApi', () => ({
  notificationApi: {
    broadcastNotification: vi.fn(),
  },
}));

describe('DSAapp Phase 9 Admin Console & Analytics UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Admin Access Gate & RBAC (AdminLayout)', () => {
    it('denies access when user is not authenticated or not ADMIN', () => {
      vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
        user: { id: 'u1', email: 'student@example.com', role: 'STUDENT' } as any,
        token: 'token',
        isAuthenticated: true,
        isPremium: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        openAuthModal: vi.fn(),
        closeAuthModal: vi.fn(),
        isAuthModalOpen: false,
        authModalMode: 'login',
      });

      const onNavigate = vi.fn();
      render(
        <AdminLayout currentPath="/admin" onNavigate={onNavigate}>
          <div>Admin Secret Content</div>
        </AdminLayout>
      );

      expect(screen.getByText('Access Denied')).toBeInTheDocument();
      expect(screen.queryByText('Admin Secret Content')).not.toBeInTheDocument();

      const returnBtn = screen.getByRole('button', { name: /Return to Platform Home/i });
      fireEvent.click(returnBtn);
      expect(onNavigate).toHaveBeenCalledWith('/');
    });

    it('renders admin sidebar and allows navigation when user is ADMIN', () => {
      vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
        user: { id: 'admin-1', email: 'admin@dsaapp.internal', role: 'ADMIN' } as any,
        token: 'admin-token',
        isAuthenticated: true,
        isPremium: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        openAuthModal: vi.fn(),
        closeAuthModal: vi.fn(),
        isAuthModalOpen: false,
        authModalMode: 'login',
      });

      const onNavigate = vi.fn();
      render(
        <AdminLayout currentPath="/admin" onNavigate={onNavigate}>
          <div>Welcome Superuser</div>
        </AdminLayout>
      );

      expect(screen.getByText('DSAapp Admin')).toBeInTheDocument();
      expect(screen.getByText('Superuser Console')).toBeInTheDocument();
      expect(screen.getByText('Welcome Superuser')).toBeInTheDocument();

      expect(screen.getByRole('button', { name: 'Overview' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Learners & Users' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Problems & Tests' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Platform Analytics' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'System Diagnostics' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Security Audit Logs' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Broadcast Alerts' })).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: 'Platform Analytics' }));
      expect(onNavigate).toHaveBeenCalledWith('/admin/analytics');
    });
  });

  describe('AdminOverviewPage', () => {
    it('renders platform KPIs and subsystem status cards', async () => {
      (adminApi.getPlatformOverview as any).mockResolvedValue({
        total_users: 1250,
        active_users_dau: 340,
        active_users_mau: 980,
        total_problems: 150,
        total_submissions: 8400,
        total_accepted_submissions: 5200,
        platform_acceptance_rate: 61.9,
        total_premium_subscribers: 75,
        total_revenue_amount: 149925,
        generated_at: new Date().toISOString(),
      });

      (adminApi.getDiagnostics as any).mockResolvedValue({
        app_name: 'DSAapp',
        app_version: '0.9.0',
        environment: 'production',
        server_time: new Date().toISOString(),
        uptime_seconds: 3600,
        database: { status: 'healthy', latency_ms: 2.5 },
        redis: { status: 'healthy', latency_ms: 0.8 },
        docker_sandbox: { status: 'healthy', version: '29.8.1', active_containers: 0 },
        judge_queue: { status: 'healthy', queue_depth: 0, active_workers: 2 },
        ai_provider: { status: 'healthy', provider: 'google-genai' },
        timestamp: new Date().toISOString(),
      });

      const onNavigate = vi.fn();
      render(<AdminOverviewPage onNavigate={onNavigate} />);

      await waitFor(() => {
        expect(screen.getByText('Platform Command Center')).toBeInTheDocument();
      });

      expect(screen.getByText('1,250')).toBeInTheDocument();
      expect(screen.getByText('340')).toBeInTheDocument();
      expect(screen.getByText('61.9%')).toBeInTheDocument();
      expect(screen.getByText('₹149,925')).toBeInTheDocument();

      expect(screen.getByText('Docker Sandbox')).toBeInTheDocument();
      expect(screen.getByText('Judge Queue')).toBeInTheDocument();
    });
  });

  describe('AdminUsersPage', () => {
    it('renders user directory and opens role elevation modal', async () => {
      (adminApi.listUsers as any).mockResolvedValue({
        items: [
          {
            id: 'u-101',
            email: 'user101@example.com',
            display_name: 'Learner One',
            role: 'STUDENT',
            is_active: true,
            is_verified: true,
            plan: 'FREE',
            premium_active: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      });

      (adminApi.getUser as any).mockResolvedValue({
        id: 'u-101',
        email: 'user101@example.com',
        display_name: 'Learner One',
        role: 'STUDENT',
        is_active: true,
        is_verified: true,
        plan: 'FREE',
        premium_active: false,
        submissions_count: 55,
        solved_problems_count: 42,
        current_streak: 5,
        total_xp: 850,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });

      render(<AdminUsersPage />);

      await waitFor(() => {
        expect(screen.getByText('user101@example.com')).toBeInTheDocument();
      });

      expect(screen.getByText('STUDENT')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();

      // Open inspection modal
      const inspectBtn = screen.getByRole('button', { name: 'Inspect' });
      fireEvent.click(inspectBtn);

      await waitFor(() => {
        expect(screen.getByText('Learner Profile Inspection')).toBeInTheDocument();
      });

      expect(screen.getByText(/Audit Reason/i)).toBeInTheDocument();
    });
  });

  describe('AdminProblemsPage', () => {
    it('renders problem list and allows viewing test cases', async () => {
      (adminApi.listProblems as any).mockResolvedValue({
        items: [
          {
            id: 'prob-1',
            public_id: 'P-101',
            slug: 'two-sum',
            title: 'Two Sum',
            difficulty: 'EASY',
            access_level: 'FREE',
            status: 'PUBLISHED',
            time_limit_ms: 2000,
            memory_limit_mb: 256,
            test_cases_count: 5,
            hidden_test_cases_count: 2,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      });

      (adminApi.listTestCases as any).mockResolvedValue([
        {
          id: 'tc-1',
          problem_id: 'prob-1',
          input: '[2,7,11,15]\n9',
          expected_output: '[0,1]',
          is_sample: true,
          is_hidden: false,
          display_order: 1,
          created_at: new Date().toISOString(),
        },
        {
          id: 'tc-2',
          problem_id: 'prob-1',
          input: '[3,2,4]\n6',
          expected_output: '[1,2]',
          is_sample: false,
          is_hidden: true,
          display_order: 2,
          created_at: new Date().toISOString(),
        },
      ]);

      render(<AdminProblemsPage />);

      await waitFor(() => {
        expect(screen.getByText('Two Sum')).toBeInTheDocument();
      });

      const testsBtn = screen.getByRole('button', { name: 'Manage Test Cases' });
      fireEvent.click(testsBtn);

      await waitFor(() => {
        expect(screen.getByText('Test Cases Studio')).toBeInTheDocument();
      });

      expect(screen.getByText('Sample')).toBeInTheDocument();
      expect(screen.getByText('Hidden Verification')).toBeInTheDocument();
    });
  });

  describe('AdminSystemPage & AdminAuditPage', () => {
    it('renders system diagnostics with zero secret leakage indicator', async () => {
      (adminApi.getDiagnostics as any).mockResolvedValue({
        app_name: 'DSAapp',
        app_version: '0.9.0',
        environment: 'production',
        server_time: new Date().toISOString(),
        status: 'healthy',
        uptime_seconds: 7200,
        database: { status: 'healthy', latency_ms: 1.2 },
        redis: { status: 'healthy', latency_ms: 0.5 },
        docker_sandbox: { status: 'healthy', version: '29.8.1', active_containers: 0 },
        judge_queue: { status: 'healthy', queue_depth: 0, active_workers: 2 },
        ai_provider: { status: 'healthy', provider: 'google-genai' },
        timestamp: new Date().toISOString(),
      });

      render(<AdminSystemPage />);

      await waitFor(() => {
        expect(screen.getByText('System Health & Diagnostics')).toBeInTheDocument();
      });

      expect(screen.getByText('Zero Secret Leakage')).toBeInTheDocument();
      expect(screen.getByText('Docker Sandboxed Execution Runtime')).toBeInTheDocument();
      expect(screen.getByText('Version: 29.8.1')).toBeInTheDocument();
    });

    it('renders audit logs list with actor and action filters', async () => {
      (adminApi.listAuditLogs as any).mockResolvedValue({
        items: [
          {
            id: 'audit-1',
            user_id: 'admin-1',
            user_email: 'admin@dsaapp.internal',
            action: 'UPDATE_ROLE',
            target_type: 'USER',
            target_id: 'u-101',
            details: { previous_role: 'STUDENT', new_role: 'CONTENT_EDITOR', reason: 'Editorial promotion' },
            ip_address: '127.0.0.1',
            created_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        page_size: 30,
        total_pages: 1,
      });

      render(<AdminAuditPage />);

      await waitFor(() => {
        expect(screen.getByText('Security & Admin Audit Trail')).toBeInTheDocument();
      });

      expect(screen.getByText('UPDATE_ROLE')).toBeInTheDocument();
      expect(screen.getByText('admin@dsaapp.internal')).toBeInTheDocument();
      expect(screen.getByText('USER')).toBeInTheDocument();
    });
  });

  describe('AdminBroadcastPage', () => {
    it('allows composing and dispatching system broadcasts', async () => {
      (notificationApi.broadcastNotification as any).mockResolvedValue({
        broadcast_id: 'bc-123',
        dispatched_notifications: 1450,
      });

      render(<AdminBroadcastPage />);

      expect(screen.getByText('Broadcast Announcements')).toBeInTheDocument();

      fireEvent.change(screen.getByPlaceholderText(/e\.g\. Weekly Contest/i), {
        target: { value: 'Scheduled Maintenance Notice' },
      });

      fireEvent.change(screen.getByPlaceholderText(/Write clear educational guidance/i), {
        target: { value: 'We will be conducting brief maintenance at 02:00 UTC.' },
      });

      const dispatchBtn = screen.getByRole('button', { name: /Send Broadcast to Learners/i });
      fireEvent.click(dispatchBtn);

      await waitFor(() => {
        expect(screen.getByText(/Broadcast Dispatched Successfully/i)).toBeInTheDocument();
      });

      expect(screen.getByText('1,450')).toBeInTheDocument();
    });
  });
});
