import { describe, expect, it } from "vitest";
import {
  EXPLORE_PARAMS,
  parseExploreParams,
  buildExploreSearchParams,
  canFetch,
  type ExploreParams,
} from "./exploreParams";

describe("exploreParams", () => {
  describe("EXPLORE_PARAMS", () => {
    it("exports RADIUS_DEFAULTS", () => {
      expect(EXPLORE_PARAMS.DEFAULT_RADIUS).toBe(0.5);
      expect(EXPLORE_PARAMS.MIN_RADIUS).toBe(0.1);
      expect(EXPLORE_PARAMS.MAX_RADIUS).toBe(3);
    });
  });

  describe("parseExploreParams", () => {
    it("parses valid params from URLSearchParams", () => {
      const sp = new URLSearchParams("q=Cambridge%2C+MA&radius=1.0");
      const result = parseExploreParams(sp);
      expect(result.params).toEqual({ q: "Cambridge, MA", radius: 1.0 });
      expect(result.validationError).toBeNull();
    });

    it("returns empty q when missing", () => {
      const sp = new URLSearchParams("radius=0.5");
      const result = parseExploreParams(sp);
      expect(result.params.q).toBe("");
      expect(result.params.radius).toBe(0.5);
    });

    it("uses DEFAULT_RADIUS when radius is missing", () => {
      const sp = new URLSearchParams("q=Boston");
      const result = parseExploreParams(sp);
      expect(result.params.radius).toBe(EXPLORE_PARAMS.DEFAULT_RADIUS);
    });

    it("passes through radius validation errors", () => {
      const sp = new URLSearchParams("q=Boston&radius=not-a-number");
      const result = parseExploreParams(sp);
      expect(result.params.q).toBe("Boston");
      expect(result.params.radius).toBe(EXPLORE_PARAMS.DEFAULT_RADIUS);
      expect(result.validationError).toBe("Radius must be a number.");
    });

    it("clamps radius to valid range", () => {
      const sp = new URLSearchParams("q=Boston&radius=5.0");
      const result = parseExploreParams(sp);
      expect(result.params.radius).toBe(EXPLORE_PARAMS.MAX_RADIUS);
    });

    it("handles empty search params", () => {
      const sp = new URLSearchParams();
      const result = parseExploreParams(sp);
      expect(result.params.q).toBe("");
      expect(result.params.radius).toBe(EXPLORE_PARAMS.DEFAULT_RADIUS);
    });

    it("preserves query string with special characters", () => {
      const sp = new URLSearchParams("q=123%20Main%20St%2C%20Boston&radius=1.0");
      const result = parseExploreParams(sp);
      expect(result.params.q).toBe("123 Main St, Boston");
    });
  });

  describe("buildExploreSearchParams", () => {
    it("builds URLSearchParams from valid params", () => {
      const params: ExploreParams = { q: "Cambridge, MA", radius: 1.0 };
      const sp = buildExploreSearchParams(params);
      expect(sp.get("q")).toBe("Cambridge, MA");
      expect(sp.get("radius")).toBe("1");
    });

    it("omits q when empty", () => {
      const params: ExploreParams = { q: "", radius: 0.5 };
      const sp = buildExploreSearchParams(params);
      expect(sp.has("q")).toBe(false);
      expect(sp.get("radius")).toBe("0.5");
    });

    it("always includes radius", () => {
      const params: ExploreParams = { q: "Boston", radius: 2.5 };
      const sp = buildExploreSearchParams(params);
      expect(sp.get("radius")).toBe("2.5");
    });

    it("round-trips with parseExploreParams", () => {
      const original: ExploreParams = { q: "Cambridge, MA", radius: 1.5 };
      const sp = buildExploreSearchParams(original);
      const parsed = parseExploreParams(sp);
      expect(parsed.params.q).toBe(original.q);
      expect(parsed.params.radius).toBe(original.radius);
    });
  });

  describe("canFetch", () => {
    it("returns true when q has content", () => {
      expect(canFetch({ q: "Boston", radius: 0.5 })).toBe(true);
      expect(canFetch({ q: "Cambridge, MA", radius: 1.0 })).toBe(true);
    });

    it("returns false when q is empty", () => {
      expect(canFetch({ q: "", radius: 0.5 })).toBe(false);
    });

    it("returns false when q is whitespace only", () => {
      expect(canFetch({ q: "   ", radius: 0.5 })).toBe(false);
      expect(canFetch({ q: "\t\n", radius: 0.5 })).toBe(false);
    });

    it("returns true when q has content after trim", () => {
      expect(canFetch({ q: "  Boston  ", radius: 0.5 })).toBe(true);
    });
  });
});
