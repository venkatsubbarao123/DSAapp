import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../App.tsx";

describe("DSAapp Premium & Entitlement Flow", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/premium");
    vi.restoreAllMocks();
  });

  it("renders Free and Pro pricing cards with authoritative pricing", () => {
    render(<App />);

    expect(
      screen.getByText("Master Algorithms with Production Rigor")
    ).toBeInTheDocument();
    expect(screen.getByText("Standard Free")).toBeInTheDocument();
    expect(screen.getByText("DSAapp Premium")).toBeInTheDocument();
    expect(screen.getByText("₹999")).toBeInTheDocument();
    expect(screen.getByText("/ 365 days")).toBeInTheDocument();
  });

  it("clicking upgrade when unauthenticated opens the AuthModal", () => {
    render(<App />);

    const upgradeBtn = screen.getByRole("button", {
      name: "Sign In to Upgrade",
    });
    fireEvent.click(upgradeBtn);

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Sign In to DSAapp" })
    ).toBeInTheDocument();
  });

  it("completes development mode payment order creation and simulation", async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: unknown) => {
      const urlStr = String(url);
      // Return authenticated free user on me
      if (urlStr.includes("/api/v1/auth/me")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                id: "usr_100",
                email: "student@example.com",
                role: "STUDENT",
                is_active: true,
                is_verified: true,
                plan: "FREE",
                premium_active: false,
              },
            }),
        });
      }
      if (urlStr.includes("/api/v1/auth/refresh")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: { access_token: "mock_jwt_token" },
            }),
        });
      }
      if (urlStr.includes("/api/v1/payments/create-order")) {
        return Promise.resolve({
          ok: true,
          status: 201,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                order_id: "ord_test_123456",
                plan_id: "plan_premium_annual",
                amount: 999,
                currency: "INR",
                status: "PENDING",
              },
            }),
        });
      }
      if (urlStr.includes("/verify")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                id: "ent_test_123",
                status: "ACTIVE",
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

    // Wait for authenticated student state to load
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Upgrade to Pro (₹999/yr)" })
      ).toBeInTheDocument();
    });

    // Create payment order
    const orderBtn = screen.getByRole("button", {
      name: "Upgrade to Pro (₹999/yr)",
    });
    fireEvent.click(orderBtn);

    // Expect order section with dev verification button
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Simulate Verified Payment (Dev Mode)" })
      ).toBeInTheDocument();
    });

    // Simulate payment completion
    const verifyBtn = screen.getByRole("button", {
      name: "Simulate Verified Payment (Dev Mode)",
    });
    fireEvent.click(verifyBtn);

    await waitFor(() => {
      expect(
        screen.getByText("Payment verified! Premium membership activated.")
      ).toBeInTheDocument();
    });
  });
});
