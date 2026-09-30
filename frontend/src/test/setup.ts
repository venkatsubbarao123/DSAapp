import "@testing-library/jest-dom";

// Mock window.scrollTo for jsdom test environment
if (typeof window !== "undefined") {
  window.scrollTo = () => {};

  if (!window.matchMedia) {
    window.matchMedia = (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    } as any);
  }
}
