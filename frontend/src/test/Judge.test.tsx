import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { SubmissionDetailPage } from "../pages/SubmissionDetailPage.tsx";

// Mock AuthContext
vi.mock("../context/AuthContext.tsx", () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: "user-1", email: "judge_ui@example.com", role: "STUDENT" },
    openAuthModal: vi.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock API client
vi.mock("../services/apiClient.ts", () => ({
  fetchApi: vi.fn(),
  APIClientError: class extends Error {},
}));

import { fetchApi } from "../services/apiClient.ts";

describe("DSAapp Phase 5 Online Judge UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders judge verdict and execution metrics on SubmissionDetailPage", async () => {
    vi.mocked(fetchApi).mockResolvedValueOnce({
      success: true,
      data: {
        id: "sub-123",
        public_id: "sub_abcdef",
        problem_id: "two-sum",
        problem_title: "Two Sum",
        problem_slug: "two-sum",
        language: "python",
        source_code: "def twoSum(): pass",
        status: "ACCEPTED",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        execution_notice: "Executed via sandbox runner.",
        result: {
          id: "res-1",
          submission_id: "sub-123",
          verdict: "ACCEPTED",
          tests_total: 10,
          tests_passed: 10,
          execution_time_ms: 45,
          memory_used_bytes: 16 * 1024 * 1024,
          compiler_output_safe: null,
          runtime_output_safe: null,
          created_at: new Date().toISOString(),
        },
      },
    });

    render(<SubmissionDetailPage submissionId="sub_abcdef" onNavigate={() => {}} />);

    // Verify Verdict header and metrics are rendered
    expect(await screen.findByText("✓ Accepted")).toBeInTheDocument();
    expect(screen.getByText("10 / 10")).toBeInTheDocument();
    expect(screen.getByText("45 ms")).toBeInTheDocument();
    expect(screen.getByText("16 MB")).toBeInTheDocument();
  });

  it("renders compilation error logs safely on SubmissionDetailPage", async () => {
    vi.mocked(fetchApi).mockResolvedValueOnce({
      success: true,
      data: {
        id: "sub-456",
        public_id: "sub_compile_err",
        problem_id: "two-sum",
        problem_title: "Two Sum",
        problem_slug: "two-sum",
        language: "cpp",
        source_code: "int main() { syntax error }",
        status: "COMPILATION_ERROR",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        result: {
          id: "res-2",
          submission_id: "sub-456",
          verdict: "COMPILATION_ERROR",
          tests_total: 5,
          tests_passed: 0,
          compiler_output_safe: "error: expected ';' before '}' token",
          created_at: new Date().toISOString(),
        },
      },
    });

    render(<SubmissionDetailPage submissionId="sub_compile_err" onNavigate={() => {}} />);

    expect(await screen.findByText("✗ COMPILATION ERROR")).toBeInTheDocument();
    expect(screen.getByText("error: expected ';' before '}' token")).toBeInTheDocument();
  });
});
