import { describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { useUrlDrivenSearch } from "./useUrlDrivenSearch";
import {
  parseExploreParams,
  buildExploreSearchParams,
  canFetch,
  type ExploreParams,
} from "../lib/exploreParams";

/** Wrapper that provides a route with query string so useSearchParams works. */
function createWrapper(initialEntry: string) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <MemoryRouter initialEntries={[initialEntry]}>
        {children}
      </MemoryRouter>
    );
  };
}

describe("useUrlDrivenSearch", () => {
  it("parses initial params from URL and returns them", () => {
    const mockFetch = vi.fn().mockResolvedValue({});
    const { result } = renderHook(
      () =>
        useUrlDrivenSearch<ExploreParams, unknown>({
          parse: parseExploreParams,
          build: buildExploreSearchParams,
          canFetch,
          fetch: mockFetch,
        }),
      { wrapper: createWrapper("/?q=Cambridge%2C+MA&radius=0.5") }
    );

    expect(result.current.params).toEqual({ q: "Cambridge, MA", radius: 0.5 });
    expect(result.current.updateDraft).toBeInstanceOf(Function);
    expect(result.current.submit).toBeInstanceOf(Function);
  });

  it("returns empty params when URL has no query", () => {
    const mockFetch = vi.fn().mockResolvedValue({});
    const { result } = renderHook(
      () =>
        useUrlDrivenSearch<ExploreParams, unknown>({
          parse: parseExploreParams,
          build: buildExploreSearchParams,
          canFetch,
          fetch: mockFetch,
        }),
      { wrapper: createWrapper("/") }
    );

    expect(result.current.params.q).toBe("");
    expect(result.current.params.radius).toBe(0.5);
  });

  it("updates validation message when draft is edited so stale errors clear", () => {
    const mockFetch = vi.fn().mockResolvedValue({});
    const { result } = renderHook(
      () =>
        useUrlDrivenSearch<ExploreParams, unknown>({
          parse: parseExploreParams,
          build: buildExploreSearchParams,
          canFetch,
          fetch: mockFetch,
        }),
      { wrapper: createWrapper("/?q=Cambridge&radius=foo") }
    );

    expect(result.current.validationMessage).toBe("Radius must be a number.");

    act(() => {
      result.current.updateDraft({ q: "Cambridge", radius: 0.5 });
    });

    expect(result.current.validationMessage).toBeNull();
    expect(result.current.params).toEqual({ q: "Cambridge", radius: 0.5 });
  });

  it("preserves trailing space in draft so multi-word queries can be typed", () => {
    const mockFetch = vi.fn().mockResolvedValue({});
    const { result } = renderHook(
      () =>
        useUrlDrivenSearch<ExploreParams, unknown>({
          parse: parseExploreParams,
          build: buildExploreSearchParams,
          canFetch,
          fetch: mockFetch,
          trimParams: (p) => ({ ...p, q: p.q.trim() }),
        }),
      { wrapper: createWrapper("/?q=New&radius=0.5") }
    );

    act(() => {
      result.current.updateDraft({ q: "New ", radius: 0.5 });
    });

    expect(result.current.params.q).toBe("New ");
  });
});
