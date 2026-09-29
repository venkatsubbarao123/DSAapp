import "@testing-library/jest-dom";

// Mock window.scrollTo for jsdom test environment
if (typeof window !== "undefined") {
  window.scrollTo = () => {};
}
