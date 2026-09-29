import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import App from "../App.tsx";

describe("DSAapp Authentication & Authorization UI", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/");
    vi.restoreAllMocks();
  });

  it("renders Sign In and Create Account buttons when unauthenticated", () => {
    render(<App />);
    expect(screen.getByRole("button", { name: "Sign In" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create Account" })).toBeInTheDocument();
  });

  it("opens AuthModal when clicking Sign In and switches to Create Account", async () => {
    render(<App />);

    const signInBtn = screen.getByRole("button", { name: "Sign In" });
    fireEvent.click(signInBtn);

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Sign In to DSAapp" })).toBeInTheDocument();

    const dialog = screen.getByRole("dialog");
    // Click switch to Create Account inside dialog footer
    const createAccountLink = within(dialog).getByRole("button", { name: "Create Account" });
    fireEvent.click(createAccountLink);

    expect(screen.getByRole("heading", { name: "Create Your DSAapp Account" })).toBeInTheDocument();
    expect(screen.getByLabelText(/Display Name/i)).toBeInTheDocument();
  });

  it("validates password strength in real time during registration", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Create Account" }));

    const passwordInput = screen.getByLabelText(/Password/i);

    // Enter short password
    fireEvent.change(passwordInput, { target: { value: "pass" } });

    expect(screen.getByText(/At least 8 characters/i)).toBeInTheDocument();
    expect(screen.getByText(/Contains at least one number/i)).toBeInTheDocument();

    // Enter valid password
    fireEvent.change(passwordInput, { target: { value: "SecurePass123" } });

    // The checks should now show green checkmarks (✓)
    expect(screen.getByText(/✓ At least 8 characters/i)).toBeInTheDocument();
    expect(screen.getByText(/✓ Contains at least one letter/i)).toBeInTheDocument();
    expect(screen.getByText(/✓ Contains at least one number/i)).toBeInTheDocument();
  });

  it("handles successful login, displays user badge, and logs out", async () => {
    // Mock successful login and me endpoints
    globalThis.fetch = vi.fn().mockImplementation((url: unknown) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/v1/auth/login")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "x-request-id": "req-login-123" }),
          json: () =>
            Promise.resolve({
              success: true,
              data: { access_token: "mock_jwt_token_123", token_type: "bearer" },
            }),
        });
      }
      if (urlStr.includes("/api/v1/auth/me")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ "x-request-id": "req-me-123" }),
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                id: "usr_123",
                email: "engineer@example.com",
                role: "STUDENT",
                is_active: true,
                is_verified: true,
                plan: "FREE",
                premium_active: false,
                profile: { display_name: "Test Engineer" },
              },
            }),
        });
      }
      if (urlStr.includes("/api/v1/auth/logout")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: () => Promise.resolve({ success: true }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: {} }),
      });
    });

    render(<App />);

    // Open modal
    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    // Fill form
    fireEvent.change(screen.getByLabelText(/Email Address/i), {
      target: { value: "engineer@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/Password/i), {
      target: { value: "SecurePass123" },
    });

    // Submit within modal dialog
    const dialog = screen.getByRole("dialog");
    const submitBtn = within(dialog).getByRole("button", { name: "Sign In" });
    fireEvent.click(submitBtn);

    // Wait for user to be authenticated in header
    await waitFor(() => {
      expect(screen.getByText("Test Engineer")).toBeInTheDocument();
      expect(screen.getByText("STUDENT")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Sign Out" })).toBeInTheDocument();
    });

    // Perform sign out
    fireEvent.click(screen.getByRole("button", { name: "Sign Out" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Sign In" })).toBeInTheDocument();
      expect(screen.queryByText("Test Engineer")).not.toBeInTheDocument();
    });
  });
});
