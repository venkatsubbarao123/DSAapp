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
          email: "student_ai@example.com",
          role: "USER",
          is_active: true,
          is_verified: true,
          profile: { display_name: "AI Learner" },
          entitlements: [],
        },
      }),
  });

describe("DSAapp Phase 6 AI Learning System UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders unauthenticated prompt when accessing /ai without login", async () => {
    window.history.pushState({}, "", "/ai");

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
      expect(screen.getByRole("heading", { name: /DSA AI Learning Assistant/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Sign In to Access AI/i })).toBeInTheDocument();
    });
  });

  it("renders authenticated AI Learning Dashboard with quota badge and tabs", async () => {
    window.history.pushState({}, "", "/ai");

    globalThis.fetch = vi.fn().mockImplementation((url: unknown) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/v1/auth/refresh")) return mockAuthRefreshSuccess();
      if (urlStr.includes("/api/v1/auth/me")) return mockAuthMeSuccess();
      if (urlStr.includes("/api/v1/ai/usage")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                daily_quota: 15,
                daily_used: 2,
                daily_remaining: 13,
                is_premium: false,
                provider: "mock",
                model: "mock-dsa-model-v1",
                can_request: true,
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
      expect(screen.getByText(/AI Learning Assistant & Tutor/i)).toBeInTheDocument();
    });

    // Check tabs
    expect(screen.getAllByRole("button", { name: "AI Tutor" }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("button", { name: "Progressive Hints" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Complexity Analyzer" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Pattern Detector" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Recommendations" })).toBeInTheDocument();


    // Check quota badge
    await waitFor(() => {
      expect(screen.getByText(/13 \/ 15 remaining/i)).toBeInTheDocument();
    });
  });

  it("interacts with AI Tutor and displays pedagogical guidance and visualizer button", async () => {
    window.history.pushState({}, "", "/ai");

    globalThis.fetch = vi.fn().mockImplementation((url: unknown, options: any) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/v1/auth/refresh")) return mockAuthRefreshSuccess();
      if (urlStr.includes("/api/v1/auth/me")) return mockAuthMeSuccess();
      if (urlStr.includes("/api/v1/ai/usage")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: { daily_quota: 15, daily_used: 1, daily_remaining: 14, is_premium: false },
            }),
        });
      }
      if (urlStr.includes("/api/v1/ai/tutor") && options?.method === "POST") {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                explanation: "Binary search eliminates half the search space at each iteration.",
                key_idea: "Calculate mid = (low + high) // 2 and narrow the bounds monotonically.",
                next_step: "Try writing the loop while low <= high.",
                visualization_suggestion: {
                  visualizer_type: "binary-search",
                  title: "Interactive Binary Search",
                  description: "Observe low, mid, high convergence.",
                },
                conversation_id: "conv-123",
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
      expect(screen.getByText(/Ask the AI Tutor/i)).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/How does binary search narrow down/i);
    fireEvent.change(input, { target: { value: "Explain binary search pointer movement" } });

    const submitBtn = screen.getByRole("button", { name: "Ask Tutor" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Binary search eliminates half the search space/i)).toBeInTheDocument();
      expect(screen.getByText(/Open Visualizer/i)).toBeInTheDocument();
    });
  });
});

