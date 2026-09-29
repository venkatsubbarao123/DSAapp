/**
 * Admin API service client for User Management, Problems & Hidden Test Cases, System Health, and Analytics
 */

import { fetchApi } from './apiClient.ts';
import {
  AdminCreateTestCaseRequest,
  AdminProblemListResponse,
  AdminTestCaseItem,
  AdminUpdateTestCaseRequest,
  AdminUpdateUserRoleRequest,
  AdminUpdateUserStatusRequest,
  AdminUserDetail,
  AdminUserListResponse,
  AuditLogListResponse,
  ComprehensiveAnalyticsResponse,
  PlatformOverviewMetrics,
  SystemDiagnosticsResponse,
  UserRole,
} from '../types/admin.ts';

export const adminApi = {
  // Users
  async listUsers(params: {
    page?: number;
    pageSize?: number;
    search?: string;
    role?: UserRole;
    isActive?: boolean;
    plan?: string;
  } = {}): Promise<AdminUserListResponse> {
    const q = new URLSearchParams();
    if (params.page) q.set('page', params.page.toString());
    if (params.pageSize) q.set('page_size', params.pageSize.toString());
    if (params.search) q.set('search', params.search);
    if (params.role) q.set('role', params.role);
    if (params.isActive !== undefined) q.set('is_active', params.isActive ? 'true' : 'false');
    if (params.plan) q.set('plan', params.plan);

    const res = await fetchApi<AdminUserListResponse>(`/api/v1/admin/users?${q.toString()}`);
    return (res as any).data ?? res;
  },

  async getUserDetail(userId: string): Promise<AdminUserDetail> {
    const res = await fetchApi<AdminUserDetail>(`/api/v1/admin/users/${userId}`);
    return (res as any).data ?? res;
  },

  async updateUserRole(userId: string, payload: AdminUpdateUserRoleRequest): Promise<AdminUserDetail> {
    const res = await fetchApi<AdminUserDetail>(`/api/v1/admin/users/${userId}/role`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return (res as any).data ?? res;
  },

  async updateUserStatus(userId: string, payload: AdminUpdateUserStatusRequest): Promise<AdminUserDetail> {
    const res = await fetchApi<AdminUserDetail>(`/api/v1/admin/users/${userId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return (res as any).data ?? res;
  },

  // Problems & Test Cases
  async listProblems(params: {
    page?: number;
    pageSize?: number;
    search?: string;
    difficulty?: string;
    statusFilter?: string;
    accessLevel?: string;
  } = {}): Promise<AdminProblemListResponse> {
    const q = new URLSearchParams();
    if (params.page) q.set('page', params.page.toString());
    if (params.pageSize) q.set('page_size', params.pageSize.toString());
    if (params.search) q.set('search', params.search);
    if (params.difficulty) q.set('difficulty', params.difficulty);
    if (params.statusFilter) q.set('status_filter', params.statusFilter);
    if (params.accessLevel) q.set('access_level', params.accessLevel);

    const res = await fetchApi<AdminProblemListResponse>(`/api/v1/admin/problems?${q.toString()}`);
    return (res as any).data ?? res;
  },

  async listTestCases(problemId: string): Promise<AdminTestCaseItem[]> {
    const res = await fetchApi<AdminTestCaseItem[]>(`/api/v1/admin/problems/${problemId}/test-cases`);
    return (res as any).data ?? res;
  },

  async createTestCase(problemId: string, payload: AdminCreateTestCaseRequest): Promise<AdminTestCaseItem> {
    const res = await fetchApi<AdminTestCaseItem>(`/api/v1/admin/problems/${problemId}/test-cases`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return (res as any).data ?? res;
  },

  async updateTestCase(testCaseId: string, payload: AdminUpdateTestCaseRequest): Promise<AdminTestCaseItem> {
    const res = await fetchApi<AdminTestCaseItem>(`/api/v1/admin/problems/test-cases/${testCaseId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    return (res as any).data ?? res;
  },

  async deleteTestCase(testCaseId: string): Promise<{ success: boolean }> {
    const res = await fetchApi<{ success: boolean }>(`/api/v1/admin/problems/test-cases/${testCaseId}`, {
      method: 'DELETE',
    });
    return (res as any).data ?? res;
  },

  // System Health & Audit
  async getDiagnostics(): Promise<SystemDiagnosticsResponse> {
    const res = await fetchApi<SystemDiagnosticsResponse>('/api/v1/admin/system/diagnostics');
    return (res as any).data ?? res;
  },

  async listAuditLogs(params: {
    page?: number;
    pageSize?: number;
    action?: string;
    actorId?: string;
    targetType?: string;
    targetId?: string;
  } = {}): Promise<AuditLogListResponse> {
    const q = new URLSearchParams();
    if (params.page) q.set('page', params.page.toString());
    if (params.pageSize) q.set('page_size', params.pageSize.toString());
    if (params.action) q.set('action', params.action);
    if (params.actorId) q.set('actor_id', params.actorId);
    if (params.targetType) q.set('target_type', params.targetType);
    if (params.targetId) q.set('target_id', params.targetId);

    const res = await fetchApi<AuditLogListResponse>(`/api/v1/admin/system/audit?${q.toString()}`);
    return (res as any).data ?? res;
  },

  // Analytics
  async getPlatformOverview(): Promise<PlatformOverviewMetrics> {
    const res = await fetchApi<PlatformOverviewMetrics>('/api/v1/admin/overview');
    return (res as any).data ?? res;
  },

  async getComprehensiveAnalytics(forceRefresh: boolean = false): Promise<ComprehensiveAnalyticsResponse> {
    const q = forceRefresh ? '?force_refresh=true' : '';
    const res = await fetchApi<ComprehensiveAnalyticsResponse>(`/api/v1/admin/comprehensive${q}`);
    return (res as any).data ?? res;
  },
};
