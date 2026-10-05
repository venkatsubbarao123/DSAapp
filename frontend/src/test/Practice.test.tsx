import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import App from "../App.tsx";

describe("DSAapp Phase 7 Practice Engine & Gamification UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders practice engine page with mode cards and drill count selector", async () => {
    window.history.pushState({}, "", "/practice");

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/health")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () => Promise.resolve({ success: true, data: { status: "healthy" } }),
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
      expect(screen.getByRole("heading", { name: "Practice Engine", level: 1 })).toBeInTheDocument();
    });

    // Check practice modes
    expect(screen.getByText("Quick Adaptive Drill")).toBeInTheDocument();
    expect(screen.getByText("Spaced Retention")).toBeInTheDocument();
    expect(screen.getByText("Weak Area Focus")).toBeInTheDocument();
    expect(screen.getByText("Mistake Reinforcement")).toBeInTheDocument();

    // Check problem count buttons
    expect(screen.getByRole("button", { name: "3 Problems" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "5 Problems" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "10 Problems" })).toBeInTheDocument();

    // Check action button
    expect(screen.getByRole("button", { name: /Start Practice Session/i })).toBeInTheDocument();
  });

  it("renders daily challenge page with challenge data and reward breakdown", async () => {
    window.history.pushState({}, "", "/daily");

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/health")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () => Promise.resolve({ success: true, data: { status: "healthy" } }),
        });
      }
      if (url.includes("/api/v1/practice/daily")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                id: "daily-1",
                challenge_date: "2026-09-29",
                problem_id: "prob-123",
                problem_title: "Invert Binary Tree",
                problem_slug: "invert-binary-tree",
                difficulty: "EASY",
                xp_reward: 50,
                bonus_xp: 25,
                solved: false,
                first_attempt_solve: false,
                xp_awarded: 0,
                can_claim: false,
              },
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: null }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Solve Today's Problem", level: 1 })).toBeInTheDocument();
    });

    expect(screen.getByText("Invert Binary Tree")).toBeInTheDocument();
    expect(screen.getByText("+50 XP")).toBeInTheDocument();
    expect(screen.getByText("+25 XP")).toBeInTheDocument();
    expect(screen.getByText("Base Solve Reward")).toBeInTheDocument();
    expect(screen.getByText("First-Attempt Bonus")).toBeInTheDocument();
  });

  it("renders achievements page with badges and tier filters", async () => {
    window.history.pushState({}, "", "/achievements");

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/health")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () => Promise.resolve({ success: true, data: { status: "healthy" } }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () =>
          Promise.resolve({
            success: true,
            data: {
              total_achievements: 12,
              unlocked_count: 3,
              achievements: [],
            },
          }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Achievements & Mastery Badges/i)).toBeInTheDocument();
    });
  });

  it("renders leaderboard page with category filters and ranking table", async () => {
    window.history.pushState({}, "", "/leaderboard");

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/health")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () => Promise.resolve({ success: true, data: { status: "healthy" } }),
        });
      }
      if (url.includes("/api/v1/leaderboards")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                category: "weekly_xp",
                total_participants: 2,
                entries: [
                  { rank: 1, user_id: "u1", display_name: "CodeMaster", score: 450, current_level: 3, current_streak: 5 },
                  { rank: 2, user_id: "u2", display_name: "ByteSolver", score: 320, current_level: 2, current_streak: 2 },
                ],
              },
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: null }),
      });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Community Leaderboards", level: 1 })).toBeInTheDocument();
    });

    // Check category buttons
    expect(screen.getByRole("button", { name: /Weekly XP/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Monthly XP/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /All-Time XP/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Weekly Solves/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Longest Streak/i })).toBeInTheDocument();

    // Check table entries
    await waitFor(() => {
      expect(screen.getByText("CodeMaster")).toBeInTheDocument();
      expect(screen.getByText("ByteSolver")).toBeInTheDocument();
    });
  });

  it("displays Phase 7 version tag and navigation links in Header", async () => {
    window.history.pushState({}, "", "/");

    globalThis.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: { status: "healthy" } }),
      })
    );

    render(<App />);

    expect(screen.getByText("v0.7.0-phase7")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Practice" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Daily" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Leaderboard" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Badges" })).toBeInTheDocument();
  });
});
