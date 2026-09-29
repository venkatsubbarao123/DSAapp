import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import App from "../App.tsx";
import { ErrorBoundary } from "../components/common/ErrorBoundary.tsx";

describe("DSAapp Frontend Foundation", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/");
  });

  it("renders the application shell and overview page", () => {
    render(<App />);
    expect(screen.getByText("DSAapp Engineering Architecture")).toBeInTheDocument();
    expect(screen.getByText("Phase 1 Foundation Operational")).toBeInTheDocument();
    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByText("System Status")).toBeInTheDocument();
  });

  it("navigates to system status page when clicking status button", async () => {
    render(<App />);
    const statusNavButton = screen.getByRole("button", { name: "System Status" });
    fireEvent.click(statusNavButton);

    expect(screen.getByText("System Vitality & Diagnostics")).toBeInTheDocument();
  });

  it("renders 404 Not Found page on unmatched route", () => {
    window.history.pushState({}, "", "/nonexistent-route");
    render(<App />);

    expect(screen.getByText("404")).toBeInTheDocument();
    expect(screen.getByText("Page Not Found")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Return to Overview" })).toBeInTheDocument();
  });

  it("ErrorBoundary catches runtime render failures and displays accessible fallback", () => {
    const ProblemChild = () => {
      throw new Error("Simulated component explosion");
    };

    render(
      <ErrorBoundary>
        <ProblemChild />
      </ErrorBoundary>
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Application Error")).toBeInTheDocument();
    expect(screen.getByText("Simulated component explosion")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reload Application" })).toBeInTheDocument();
  });
});
