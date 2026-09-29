import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AuthProvider } from "../context/AuthContext.tsx";
import { AppContent } from "../App.tsx";
import { ContestsPage } from "../pages/ContestsPage.tsx";
import { ContestDetailPage } from "../pages/ContestDetailPage.tsx";
import { InterviewPage } from "../pages/InterviewPage.tsx";
import { CompetitivePage } from "../pages/CompetitivePage.tsx";
import { SqlPracticePage } from "../pages/SqlPracticePage.tsx";
import { OopPage } from "../pages/OopPage.tsx";
import * as apiClient from "../services/apiClient.ts";

vi.mock("../services/apiClient.ts", async () => {
  const actual = await vi.importActual("../services/apiClient.ts");
  return {
    ...actual,
    fetchApi: vi.fn(),
  };
});

describe("DSAapp Phase 8 Contests, Interview, CP, SQL & OOP UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("displays Phase 8 navigation items in Header", async () => {
    (apiClient.fetchApi as any).mockResolvedValue({
      data: { status: "healthy" },
    });

    render(
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    );

    expect(screen.getByRole("button", { name: "Contests" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Interview" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "SQL" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "OOP" })).toBeInTheDocument();
  });

  it("renders ContestsPage with live, upcoming, and past tabs and registration badge", async () => {
    (apiClient.fetchApi as any).mockImplementation((url: string) => {
      if (url.includes("/api/v1/contests")) {
        return Promise.resolve({
          data: [
            {
              id: "c-1",
              title: "Weekly Rated Contest 42",
              slug: "weekly-42",
              description: "Weekly algorithmic challenge with rating updates",
              status: "LIVE",
              start_at: new Date(Date.now() - 3600000).toISOString(),
              end_at: new Date(Date.now() + 3600000).toISOString(),
              duration_seconds: 7200,
              remaining_seconds: 3500,
              visibility: "PUBLIC",
              premium_required: false,
              participant_count: 142,
            },
          ],
        });
      }
      return Promise.resolve({ data: null });
    });

    const mockNavigate = vi.fn();

    render(
      <AuthProvider>
        <ContestsPage onNavigate={mockNavigate} />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Weekly Rated Contest 42")).toBeInTheDocument();
    });

    expect(screen.getByText("LIVE")).toBeInTheDocument();
    expect(screen.getByText("Enter Arena →")).toBeInTheDocument();

    // Switch tab to Upcoming
    fireEvent.click(screen.getByText("⏳ Upcoming Contests"));
    expect(apiClient.fetchApi).toHaveBeenCalledWith(expect.stringContaining("status=UPCOMING"));
  });

  it("renders ContestDetailPage with problem list, countdown timer, and standings", async () => {
    (apiClient.fetchApi as any).mockImplementation((url: string) => {
      if (url.endsWith("/leaderboard")) {
        return Promise.resolve({
          data: {
            contest_id: "c-1",
            contest_title: "Weekly Rated Contest 42",
            status: "LIVE",
            total_participants: 2,
            entries: [
              {
                rank: 1,
                display_name: "Grandmaster_Alex",
                score: 200,
                penalty: 45,
                problems_solved: 2,
                problem_results: {},
              },
            ],
          },
        });
      }
      if (url.includes("/api/v1/contests/weekly-42")) {
        return Promise.resolve({
          data: {
            id: "c-1",
            title: "Weekly Rated Contest 42",
            slug: "weekly-42",
            description: "Live arena round",
            status: "LIVE",
            start_at: new Date(Date.now() - 1000).toISOString(),
            end_at: new Date(Date.now() + 3600000).toISOString(),
            duration_seconds: 7200,
            remaining_seconds: 3590,
            visibility: "PUBLIC",
            premium_required: false,
            participant_count: 142,
            is_registered: true,
            my_score: 100,
            my_penalty: 20,
            my_rank: 2,
            problems: [
              {
                id: "cp-1",
                problem_id: "p-1",
                title: "Prefix Sum Queries",
                slug: "prefix-sum-queries",
                sequence: 1,
                points: 100,
                penalty_minutes: 20,
                difficulty: "EASY",
                solved: true,
                wrong_attempts: 0,
              },
            ],
          },
        });
      }
      return Promise.resolve({ data: null });
    });

    const mockNavigate = vi.fn();

    render(
      <AuthProvider>
        <ContestDetailPage slug="weekly-42" onNavigate={mockNavigate} />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getAllByText("Prefix Sum Queries")[0]).toBeInTheDocument();
    });

    expect(screen.getByText(/Score value:/)).toBeInTheDocument();
    expect(screen.getByText("Standings & Leaderboard")).toBeInTheDocument();

    // Check switching to Standings tab
    fireEvent.click(screen.getByText("Standings & Leaderboard"));
    await waitFor(() => {
      expect(screen.getByText("Grandmaster_Alex")).toBeInTheDocument();
    });
  });

  it("renders InterviewPage with 7 interview tracks and customization options", async () => {
    (apiClient.fetchApi as any).mockResolvedValue({ data: [] });

    const mockNavigate = vi.fn();

    render(
      <AuthProvider>
        <InterviewPage onNavigate={mockNavigate} />
      </AuthProvider>
    );

    expect(screen.getByText("Full Technical Mock")).toBeInTheDocument();
    expect(screen.getByText("FAANG / Big Tech Drill")).toBeInTheDocument();
    expect(screen.getByText("System Architecture & Design")).toBeInTheDocument();
    expect(screen.getByText("Rapid Fire DSA Blitz")).toBeInTheDocument();
    expect(screen.getByText("Startup & Pragmatic Eng")).toBeInTheDocument();
    expect(screen.getByText("Collaborative Pair Coding")).toBeInTheDocument();
    expect(screen.getByText("Behavioral & STAR Method")).toBeInTheDocument();
    expect(screen.getByText("Begin Interview 🚀")).toBeInTheDocument();
  });

  it("renders CompetitivePage with rating bands, problem ladder, and global leaderboard", async () => {
    (apiClient.fetchApi as any).mockImplementation((url: string) => {
      if (url.includes("/bands")) {
        return Promise.resolve({
          data: [
            { name: "DIV_4", min_rating: 800, max_rating: 1199, color: "#94a3b8", problem_count: 10 },
            { name: "DIV_3", min_rating: 1200, max_rating: 1599, color: "#3b82f6", problem_count: 15 },
          ],
        });
      }
      if (url.includes("/leaderboard")) {
        return Promise.resolve({
          data: [
            {
              rank: 1,
              user_id: "u-1",
              display_name: "CodeNinja",
              current_rating: 2450,
              max_rating: 2500,
              contests_attended: 28,
              rank_title: "Grandmaster",
            },
          ],
        });
      }
      if (url.includes("/competitive/problems")) {
        return Promise.resolve({
          data: [
            {
              id: "cp-1",
              problem_id: "p-1",
              title: "Watermelon Distribution",
              slug: "watermelon-distribution",
              rating: 800,
              rating_band: "DIV_4",
              tags: ["math", "brute force"],
              platform: "Codeforces",
              cf_contest_id: 4,
              cf_index: "A",
              solved_count: 5300,
              solved_by_user: true,
            },
          ],
        });
      }
      return Promise.resolve({ data: null });
    });

    const mockNavigate = vi.fn();

    render(
      <AuthProvider>
        <CompetitivePage onNavigate={mockNavigate} />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Watermelon Distribution")).toBeInTheDocument();
    });

    expect(screen.getByText("★ 800")).toBeInTheDocument();
    expect(screen.getByText("✓ Solved")).toBeInTheDocument();

    // Check leaderboard tab
    fireEvent.click(screen.getByText("Global Competitive Leaderboard"));
    await waitFor(() => {
      expect(screen.getByText("CodeNinja")).toBeInTheDocument();
      expect(screen.getByText("Grandmaster")).toBeInTheDocument();
    });
  });

  it("renders SqlPracticePage with schema inspector, AST firewall notice, and query execution", async () => {
    (apiClient.fetchApi as any).mockImplementation((url: string) => {
      if (url === "/api/v1/sql/problems") {
        return Promise.resolve({
          data: [
            {
              id: "sql-1",
              title: "Second Highest Salary",
              slug: "second-highest-salary",
              category: "Aggregations",
              difficulty: "MEDIUM",
              concepts: ["MAX", "Subquery"],
              solved_count: 320,
              is_solved: false,
            },
          ],
        });
      }
      if (url.includes("/api/v1/sql/problems/second-highest-salary")) {
        return Promise.resolve({
          data: {
            id: "sql-1",
            title: "Second Highest Salary",
            slug: "second-highest-salary",
            category: "Aggregations",
            difficulty: "MEDIUM",
            concepts: ["MAX", "Subquery"],
            solved_count: 320,
            is_solved: false,
            description: "Write a SQL query to find the second highest salary from the Employee table.",
            schema_ddl: "CREATE TABLE Employee (id INT, salary INT);",
            seed_sql: "INSERT INTO Employee VALUES (1, 100), (2, 200), (3, 300);",
            parsed_schemas: [
              {
                table_name: "Employee",
                columns: [
                  { name: "id", type: "INT", is_pk: true },
                  { name: "salary", type: "INT", is_pk: false },
                ],
              },
            ],
            hints: ["Use DISTINCT and ORDER BY DESC with OFFSET."],
          },
        });
      }
      return Promise.resolve({ data: null });
    });

    const mockNavigate = vi.fn();

    render(
      <AuthProvider>
        <SqlPracticePage onNavigate={mockNavigate} />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Run Query 🚀")).toBeInTheDocument();
    });

    expect(screen.getByText(/Table:/)).toBeInTheDocument();
    expect(screen.getByText(/AST Firewall Active/)).toBeInTheDocument();
  });

  it("renders OopPage with Four Pillars, SOLID principles with code diffs, and GoF patterns", async () => {
    (apiClient.fetchApi as any).mockImplementation((url: string) => {
      if (url.includes("/api/v1/oop/overview")) {
        return Promise.resolve({
          data: {
            pillars: [
              {
                id: "encapsulation",
                name: "Encapsulation",
                summary: "Bundling data and methods with access restrictions.",
                explanation: "Encapsulation safeguards internal object state.",
                code_examples: {
                  python: "class BankAccount:\n    def __init__(self):\n        self.__balance = 0",
                  java: "public class BankAccount { private double balance; }",
                },
                common_pitfalls: ["Exposing raw mutable collections."],
              },
            ],
            solid_principles: [
              {
                letter: "S",
                name: "Single Responsibility Principle",
                summary: "A class should have one, and only one, reason to change.",
                bad_example: { python: "class Order: def process(); def save_to_db();" },
                good_example: { python: "class Order: pass\nclass OrderRepository: pass" },
                benefits: ["High cohesion", "Low coupling"],
              },
            ],
            design_patterns: [
              {
                name: "Factory Method",
                category: "CREATIONAL",
                intent: "Defines an interface for creating objects.",
                use_cases: ["Plugin frameworks"],
                structure_diagram_mermaid: "classDiagram",
                implementation: { python: "class DialogFactory: pass" },
                tradeoffs: ["Proliferation of subclasses."],
              },
            ],
          },
        });
      }
      return Promise.resolve({ data: null });
    });

    const mockNavigate = vi.fn();

    render(
      <AuthProvider>
        <OopPage onNavigate={mockNavigate} />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getAllByText("Encapsulation")[0]).toBeInTheDocument();
    });

    expect(screen.getByText("Encapsulation safeguards internal object state.")).toBeInTheDocument();
    expect(screen.getByText("Four Pillars of OOP")).toBeInTheDocument();
    expect(screen.getByText("SOLID Principles")).toBeInTheDocument();
    expect(screen.getByText("GoF Design Patterns")).toBeInTheDocument();

    // Check SOLID tab
    fireEvent.click(screen.getByText("SOLID Principles"));
    expect(screen.getAllByText("Single Responsibility Principle")[0]).toBeInTheDocument();
    expect(screen.getByText("❌ Violation (Bad)")).toBeInTheDocument();
    expect(screen.getByText("✅ Refactored (Good)")).toBeInTheDocument();

    // Check GoF Design Patterns tab
    fireEvent.click(screen.getByText("GoF Design Patterns"));
    expect(screen.getAllByText("Factory Method")[0]).toBeInTheDocument();
    expect(screen.getAllByText("CREATIONAL")[0]).toBeInTheDocument();
  });
});
