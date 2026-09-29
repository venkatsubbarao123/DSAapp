import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../App.tsx";

describe("DSAapp Phase 6 DSA Visualizers Engine & UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders visualizers page with catalog and default binary search visualizer", async () => {
    window.history.pushState({}, "", "/visualizers");

    globalThis.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: { status: "healthy" } }),
      })
    );

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/DSA Algorithm & Structure Visualizers/i)).toBeInTheDocument();
    });

    // Check catalog contains all categories
    expect(screen.getByRole("button", { name: "Fundamentals" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Algorithms" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Trees & Graphs" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Patterns" })).toBeInTheDocument();

    // Check initial visualizer is loaded
    expect(screen.getByRole("heading", { name: "Binary Search", level: 2 })).toBeInTheDocument();
    expect(screen.getByText(/Step 1 of/i)).toBeInTheDocument();
  });


  it("steps forward and backward through algorithm animation frames deterministically", async () => {
    window.history.pushState({}, "", "/visualizers");

    globalThis.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: { status: "healthy" } }),
      })
    );

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Step 1 of/i)).toBeInTheDocument();
    });

    // Click Next
    const nextBtn = screen.getByRole("button", { name: /Next >/i });
    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(screen.getByText(/Step 2 of/i)).toBeInTheDocument();
    });

    // Click Prev
    const prevBtn = screen.getByRole("button", { name: /< Prev/i });
    fireEvent.click(prevBtn);

    await waitFor(() => {
      expect(screen.getByText(/Step 1 of/i)).toBeInTheDocument();
    });
  });

  it("filters visualizer catalog by category", async () => {
    window.history.pushState({}, "", "/visualizers");

    globalThis.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => Promise.resolve({ success: true, data: { status: "healthy" } }),
      })
    );

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/DSA Algorithm & Structure Visualizers/i)).toBeInTheDocument();
    });

    // Click Patterns filter
    const patternsBtn = screen.getByRole("button", { name: "Patterns" });
    fireEvent.click(patternsBtn);

    await waitFor(() => {
      expect(screen.getByText(/Two Pointers Pattern/i)).toBeInTheDocument();
      expect(screen.getByText(/Sliding Window Pattern/i)).toBeInTheDocument();
    });
  });
});
