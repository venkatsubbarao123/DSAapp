import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../App.tsx";

describe("DSAapp Curriculum, Topics, Lessons & Problems UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the Curriculum pathways page with published curricula", async () => {
    window.history.pushState({}, "", "/curriculum");

    globalThis.fetch = vi.fn().mockImplementation((url: unknown) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/v1/curricula")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: [
                {
                  id: "cur_1",
                  public_id: "cur_abc",
                  slug: "core-dsa-seed",
                  title: "Core Data Structures & Algorithms",
                  short_description: "Foundational algorithmic concepts.",
                  level: "BEGINNER",
                  status: "PUBLISHED",
                  display_order: 1,
                  is_free: true,
                },
              ],
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: [] }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Structured Learning Pathways")).toBeInTheDocument();
      expect(screen.getByText("Core Data Structures & Algorithms")).toBeInTheDocument();
      expect(screen.getByText("FREE ACCESS")).toBeInTheDocument();
    });
  });

  it("renders Problems directory with difficulty tags and filters", async () => {
    window.history.pushState({}, "", "/problems");

    globalThis.fetch = vi.fn().mockImplementation((url: unknown) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/v1/problems")) {
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
                    id: "p_1",
                    public_id: "prb_1",
                    slug: "two-sum-seed",
                    title: "Two Sum",
                    difficulty: "EASY",
                    access_level: "FREE",
                    status: "PUBLISHED",
                    display_order: 1,
                    estimated_minutes: 15,
                    tags: [{ id: "t_1", slug: "array", name: "Array" }],
                    patterns: [{ id: "pat_1", slug: "two-pointers", name: "Two Pointers" }],
                  },
                ],
                total: 1,
                page: 1,
                page_size: 15,
                total_pages: 1,
                has_next: false,
                has_prev: false,
              },
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: [] }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Algorithmic Problem Directory")).toBeInTheDocument();
      expect(screen.getByText("Two Sum")).toBeInTheDocument();
      expect(screen.getAllByText("EASY").length).toBeGreaterThanOrEqual(2);
      expect(screen.getByText("Two Pointers")).toBeInTheDocument();
    });
  });

  it("renders Problem Detail view with constraints, examples, sample test cases, and hints", async () => {
    window.history.pushState({}, "", "/problems/two-sum-seed");

    globalThis.fetch = vi.fn().mockImplementation((url: unknown) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/v1/problems/two-sum-seed")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                id: "p_1",
                public_id: "prb_1",
                slug: "two-sum-seed",
                title: "Two Sum",
                statement: "Given an array of integers nums and an integer target...",
                difficulty: "EASY",
                access_level: "FREE",
                status: "PUBLISHED",
                display_order: 1,
                estimated_minutes: 15,
                constraints: "2 <= nums.length <= 10^4",
                supported_languages: ["python", "java"],
                version: 1,
                examples: [
                  {
                    id: "ex_1",
                    input: "nums = [2,7,11,15], target = 9",
                    output: "[0,1]",
                    explanation: "2 + 7 = 9",
                    display_order: 1,
                  },
                ],
                hints: [
                  {
                    id: "h_1",
                    hint_number: 1,
                    title: "Complements",
                    content: "Look for target - x in a hash map.",
                    is_premium: false,
                  },
                ],
                sample_test_cases: [
                  {
                    id: "tc_1",
                    input: "[2, 7, 11, 15]\n9",
                    expected_output: "[0, 1]",
                    is_sample: true,
                    display_order: 1,
                  },
                ],
                tags: [{ id: "t_1", slug: "array", name: "Array" }],
                patterns: [{ id: "pat_1", slug: "two-pointers", name: "Two Pointers" }],
              },
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: [] }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Two Sum")).toBeInTheDocument();
      expect(screen.getByText("Problem Description")).toBeInTheDocument();
      expect(screen.getByText(/2 <= nums.length <= 10\^4/i)).toBeInTheDocument();
      expect(screen.getByText("Sample Verification Cases")).toBeInTheDocument();
      expect(screen.getByText(/💡 Hint 1: Complements/i)).toBeInTheDocument();
    });

    // Reveal hint
    fireEvent.click(screen.getByText(/💡 Hint 1: Complements/i));
    expect(screen.getByText("Look for target - x in a hash map.")).toBeInTheDocument();
  });

  it("displays Premium Gate when a Free user attempts to access a locked Premium problem", async () => {
    window.history.pushState({}, "", "/problems/longest-substring-seed");

    globalThis.fetch = vi.fn().mockImplementation((url: unknown) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/v1/problems/longest-substring-seed")) {
        return Promise.resolve({
          ok: false,
          status: 403,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: false,
              error: {
                code: "HTTP_403",
                message: "This problem requires an active Premium subscription.",
              },
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: [] }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("region", { name: "Premium Content Gate" })).toBeInTheDocument();
      expect(screen.getByText("DSAapp Pro Problem")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Upgrade to Pro \(₹999\/yr\)/i })).toBeInTheDocument();
    });
  });

  it("renders Lesson page with structured blocks (XSS immune)", async () => {
    window.history.pushState({}, "", "/lessons/dynamic-arrays-seed");

    globalThis.fetch = vi.fn().mockImplementation((url: unknown) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/v1/lessons/dynamic-arrays-seed")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                id: "les_1",
                public_id: "les_abc",
                subtopic_id: "sub_1",
                slug: "dynamic-arrays-seed",
                title: "Dynamic Arrays & Amortized Complexity",
                summary: "Memory layouts and resizing amortized analysis.",
                estimated_minutes: 15,
                difficulty: "BEGINNER",
                display_order: 1,
                access_level: "FREE",
                status: "PUBLISHED",
                version: 1,
                blocks: [
                  {
                    type: "heading",
                    level: 1,
                    content: "Understanding Dynamic Arrays",
                  },
                  {
                    type: "paragraph",
                    content: "A dynamic array is a contiguous memory structure...",
                  },
                  {
                    type: "code",
                    language: "python",
                    content: "arr = [1, 2, 3]",
                  },
                ],
              },
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: [] }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Dynamic Arrays & Amortized Complexity")).toBeInTheDocument();
      expect(screen.getByText("Understanding Dynamic Arrays")).toBeInTheDocument();
      expect(screen.getByText("A dynamic array is a contiguous memory structure...")).toBeInTheDocument();
      expect(screen.getByText("arr = [1, 2, 3]")).toBeInTheDocument();
    });
  });
});
