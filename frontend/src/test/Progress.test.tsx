import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../App.tsx";

const mockAuthRefreshSuccess = () =>
  Promise.resolve({
    ok: true,
    status: 200,
    headers: new Headers(),
    json: () =>
      Promise.resolve({
        success: true,
        data: { access_token: "mock_jwt_token_123", token_type: "bearer" },
      }),
  });

const mockAuthMeSuccess = () =>
  Promise.resolve({
    ok: true,
    status: 200,
    headers: new Headers(),
    json: () =>
      Promise.resolve({
        success: true,
        data: {
          id: "user_test",
          email: "student@example.com",
          role: "USER",
          is_active: true,
          is_verified: true,
          profile: { display_name: "Algorithm Student" },
          entitlements: [],
        },
      }),
  });

describe("DSAapp Phase 4 Progress, Submissions, Mistakes & Revision UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders unauthenticated prompt when accessing /progress without login", async () => {
    window.history.pushState({}, "", "/progress");

    globalThis.fetch = vi.fn().mockImplementation((url: unknown) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/v1/auth/refresh") || urlStr.includes("/api/v1/auth/me")) {
        return Promise.reject(new Error("Unauthorized"));
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: { status: "healthy" } }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Track Your DSA Learning Journey")).toBeInTheDocument();
      expect(screen.getByText("Sign In to View Progress")).toBeInTheDocument();
    });
  });

  it("renders authenticated ProgressPage with mathematical metrics and topic breakdown", async () => {
    window.history.pushState({}, "", "/progress");

    globalThis.fetch = vi.fn().mockImplementation((url: unknown) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/v1/auth/refresh")) {
        return mockAuthRefreshSuccess();
      }
      if (urlStr.includes("/api/v1/auth/me")) {
        return mockAuthMeSuccess();
      }
      if (urlStr.includes("/api/v1/progress/overview")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                lessons_started: 4,
                lessons_completed: 3,
                total_visible_lessons: 10,
                lesson_completion_percent: 30.0,
                problems_attempted: 5,
                problems_solved: 3,
                total_visible_problems: 15,
                problem_solving_percent: 20.0,
                overall_completion_percent: 24.0,
                recent_activity: [
                  {
                    title: "Two Sum",
                    entity_type: "PROBLEM",
                    slug: "two-sum",
                    status: "ATTEMPTED",
                    timestamp: "2026-09-29T10:00:00Z",
                  },
                ],
                due_revisions_count: 2,
                unresolved_mistakes_count: 1,
              },
            }),
        });
      }
      if (urlStr.includes("/api/v1/progress/topics")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: [
                {
                  topic_id: "top_arr",
                  topic_title: "Arrays & Dynamic Arrays",
                  topic_slug: "arrays",
                  total_lessons: 5,
                  completed_lessons: 2,
                  total_problems: 8,
                  solved_problems: 2,
                  completion_percent: 30.8,
                },
              ],
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: { status: "healthy" } }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Learning Progress & Metrics")).toBeInTheDocument();
      expect(screen.getByText("24%")).toBeInTheDocument();
      expect(screen.getByText("Arrays & Dynamic Arrays")).toBeInTheDocument();
      expect(screen.getByText("Two Sum")).toBeInTheDocument();
    });
  });

  it("renders SubmissionsPage with zero-trust architectural execution notice and history list", async () => {
    window.history.pushState({}, "", "/submissions");

    globalThis.fetch = vi.fn().mockImplementation((url: unknown) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/v1/auth/refresh")) {
        return mockAuthRefreshSuccess();
      }
      if (urlStr.includes("/api/v1/auth/me")) {
        return mockAuthMeSuccess();
      }
      if (urlStr.includes("/api/v1/submissions")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                items: [
                  {
                    id: "sub_1",
                    public_id: "sub_pub_123",
                    problem_id: "prob_1",
                    problem_title: "Valid Anagram",
                    problem_slug: "valid-anagram",
                    language: "python",
                    status: "QUEUED_FOR_FUTURE_JUDGE",
                    created_at: "2026-09-29T10:15:00Z",
                    execution_notice: "Queued for containerized execution.",
                  },
                ],
                total: 1,
                skip: 0,
                limit: 50,
              },
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: { status: "healthy" } }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Submission History")).toBeInTheDocument();
      expect(
        screen.getByText("Zero-Trust Architectural Invariant: Submissions are Queued")
      ).toBeInTheDocument();
      expect(screen.getByText("Valid Anagram")).toBeInTheDocument();
      expect(screen.getByText("QUEUED FOR FUTURE JUDGE")).toBeInTheDocument();
    });
  });

  it("renders MistakesPage with filters and modal for documenting cognitive errors", async () => {
    window.history.pushState({}, "", "/mistakes");

    globalThis.fetch = vi.fn().mockImplementation((url: unknown) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/v1/auth/refresh")) {
        return mockAuthRefreshSuccess();
      }
      if (urlStr.includes("/api/v1/auth/me")) {
        return mockAuthMeSuccess();
      }
      if (urlStr.includes("/api/v1/mistakes")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                items: [
                  {
                    id: "mst_1",
                    public_id: "mst_pub_999",
                    user_id: "user_test",
                    mistake_type: "LOGIC_ERROR",
                    title: "Off-by-one pointer initialization",
                    description: "Set right pointer to len(arr) instead of len(arr) - 1.",
                    correction: "Always double-check right bound inclusion.",
                    is_resolved: false,
                    created_at: "2026-09-29T09:30:00Z",
                    updated_at: "2026-09-29T09:30:00Z",
                  },
                ],
                total: 1,
              },
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: { status: "healthy" } }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Mistake Notebook")).toBeInTheDocument();
      expect(screen.getByText("Off-by-one pointer initialization")).toBeInTheDocument();
      expect(screen.getByText("OPEN")).toBeInTheDocument();
      expect(screen.getByText("Mark Resolved")).toBeInTheDocument();
    });

    // Open modal
    fireEvent.click(screen.getByRole("button", { name: /Record New Mistake/i }));
    expect(screen.getByText("Title / Concept Summary *")).toBeInTheDocument();
  });

  it("renders Spaced RevisionPage with due items and rating actions", async () => {
    window.history.pushState({}, "", "/revision");

    globalThis.fetch = vi.fn().mockImplementation((url: unknown) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/v1/auth/refresh")) {
        return mockAuthRefreshSuccess();
      }
      if (urlStr.includes("/api/v1/auth/me")) {
        return mockAuthMeSuccess();
      }
      if (urlStr.includes("/api/v1/revision/queue")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                items: [
                  {
                    id: "rev_1",
                    public_id: "rev_pub_001",
                    source_type: "PROBLEM",
                    source_id: "two-sum",
                    title: "Two Sum Hash Map Pattern",
                    priority: 5,
                    is_active: true,
                    created_at: "2026-09-29T08:00:00Z",
                    is_overdue: false,
                    is_due_now: true,
                    schedule: {
                      id: "sched_1",
                      due_at: "2026-09-29T10:00:00Z",
                      review_count: 1,
                      interval_days: 1,
                      ease_factor: 2.5,
                      status: "ACTIVE",
                    },
                  },
                ],
                due_items_count: 1,
                total_active_items: 3,
              },
            }),
        });
      }
      if (urlStr.includes("/api/v1/revision/items/rev_1/review")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                id: "sched_1",
                due_at: "2026-10-02T10:00:00Z",
                review_count: 2,
                interval_days: 3,
                ease_factor: 2.6,
                status: "ACTIVE",
              },
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: { status: "healthy" } }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Spaced Revision Queue")).toBeInTheDocument();
      expect(screen.getByText("Two Sum Hash Map Pattern")).toBeInTheDocument();
      expect(screen.getByText("Good (+50%)")).toBeInTheDocument();
    });

    // Trigger review
    fireEvent.click(screen.getByText("Good (+50%)"));

    await waitFor(() => {
      expect(
        screen.getByText(/Reviewed "Two Sum Hash Map Pattern" as GOOD/i)
      ).toBeInTheDocument();
    });
  });

  it("submits solution code from ProblemDetailPage and shows queued non-execution feedback", async () => {
    window.history.pushState({}, "", "/problems/two-sum");

    globalThis.fetch = vi.fn().mockImplementation((url: unknown, options?: RequestInit) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/v1/auth/refresh")) {
        return mockAuthRefreshSuccess();
      }
      if (urlStr.includes("/api/v1/auth/me")) {
        return mockAuthMeSuccess();
      }
      if (urlStr.includes("/api/v1/problems/two-sum")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                id: "prob_two_sum",
                public_id: "prob_pub_2sum",
                slug: "two-sum",
                title: "Two Sum",
                statement: "Given an array of integers, return indices of the two numbers such that they add up to target.",
                difficulty: "EASY",
                status: "PUBLISHED",
                access_level: "FREE",
                patterns: [{ id: "p1", name: "Hash Map", slug: "hash-map" }],
                tags: [{ id: "t1", name: "Array", slug: "array" }],
                hints: [],
                examples: [],
                sample_test_cases: [],
              },
            }),
        });
      }
      if (urlStr.includes("/api/v1/progress/problems/prob_two_sum")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                id: "prog_1",
                problem_id: "prob_two_sum",
                status: "NOT_STARTED",
                attempts_count: 0,
                successful_attempts: 0,
                bookmarked: false,
                created_at: "2026-09-29T10:00:00Z",
                updated_at: "2026-09-29T10:00:00Z",
              },
            }),
        });
      }
      if (urlStr.includes("/api/v1/submissions") && options?.method === "POST") {
        return Promise.resolve({
          ok: true,
          status: 201,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                id: "sub_1",
                public_id: "sub_pub_verified",
                problem_id: "prob_two_sum",
                problem_title: "Two Sum",
                problem_slug: "two-sum",
                language: "python",
                source_code: "def solve(): pass",
                status: "QUEUED_FOR_FUTURE_JUDGE",
                created_at: "2026-09-29T10:30:00Z",
                updated_at: "2026-09-29T10:30:00Z",
                execution_notice:
                  "Submission stored securely and queued for future judge execution.",
              },
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: { status: "healthy" } }),
      });
    });

    render(<App />);

    console.log("RENDERED HTML:", document.body.innerHTML);
    await waitFor(() => {
      expect(screen.getByText("Two Sum")).toBeInTheDocument();
      expect(screen.getByText("Submit Solution Code")).toBeInTheDocument();
      expect(screen.getByText("Status: NOT_STARTED (Attempts: 0)")).toBeInTheDocument();
    });

    // Click submit
    fireEvent.click(screen.getByText("Submit Code (Queue for Judge)"));

    await waitFor(() => {
      expect(screen.getByText("✓ Submission Received & Queued!")).toBeInTheDocument();
      expect(screen.getByText("Status: ATTEMPTED (Attempts: 1)")).toBeInTheDocument();
    });
  });
});
