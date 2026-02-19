import { describe, expect, it } from "vitest";
import {
  COMPARE_PARAMS,
  parseCompareParams,
  buildCompareSearchParams,
  canFetchCompare,
  type CompareParams,
} from "./compareParams";

describe("compareParams", () => {
  describe("COMPARE_PARAMS", () => {
    it("exports RADIUS_DEFAULTS", () => {
      expect(COMPARE_PARAMS.DEFAULT_RADIUS).toBe(0.5);
      expect(COMPARE_PARAMS.MIN_RADIUS).toBe(0.1);
      expect(COMPARE_PARAMS.MAX_RADIUS).toBe(3);
    });
  });

  describe("parseCompareParams", () => {
    it("parses valid params from URLSearchParams", () => {
      const sp = new URLSearchParams("a=Cambridge%2C+MA&b=Boston&radius=1.0");
      const result = parseCompareParams(sp);
      expect(result.params).toEqual({ a: "Cambridge, MA", b: "Boston", radius: 1.0 });
      expect(result.validationError).toBeNull();
    });

    it("returns empty strings when a or b are missing", () => {
      const sp = new URLSearchParams("a=Cambridge&radius=0.5");
      const result = parseCompareParams(sp);
      expect(result.params.a).toBe("Cambridge");
      expect(result.params.b).toBe("");
      expect(result.params.radius).toBe(0.5);
    });

    it("uses DEFAULT_RADIUS when radius is missing", () => {
      const sp = new URLSearchParams("a=Cambridge&b=Boston");
      const result = parseCompareParams(sp);
      expect(result.params.radius).toBe(COMPARE_PARAMS.DEFAULT_RADIUS);
    });

    it("passes through radius validation errors", () => {
      const sp = new URLSearchParams("a=Cambridge&b=Boston&radius=invalid");
      const result = parseCompareParams(sp);
      expect(result.params.a).toBe("Cambridge");
      expect(result.params.b).toBe("Boston");
      expect(result.params.radius).toBe(COMPARE_PARAMS.DEFAULT_RADIUS);
      expect(result.validationError).toBe("Radius must be a number.");
    });

    it("clamps radius to valid range", () => {
      const sp = new URLSearchParams("a=Cambridge&b=Boston&radius=10.0");
      const result = parseCompareParams(sp);
      expect(result.params.radius).toBe(COMPARE_PARAMS.MAX_RADIUS);
    });

    it("handles empty search params", () => {
      const sp = new URLSearchParams();
      const result = parseCompareParams(sp);
      expect(result.params.a).toBe("");
      expect(result.params.b).toBe("");
      expect(result.params.radius).toBe(COMPARE_PARAMS.DEFAULT_RADIUS);
    });
  });

  describe("buildCompareSearchParams", () => {
    it("builds URLSearchParams from valid params", () => {
      const params: CompareParams = { a: "Cambridge, MA", b: "Boston", radius: 1.0 };
      const sp = buildCompareSearchParams(params);
      expect(sp.get("a")).toBe("Cambridge, MA");
      expect(sp.get("b")).toBe("Boston");
      expect(sp.get("radius")).toBe("1");
    });

    it("omits a when empty", () => {
      const params: CompareParams = { a: "", b: "Boston", radius: 0.5 };
      const sp = buildCompareSearchParams(params);
      expect(sp.has("a")).toBe(false);
      expect(sp.get("b")).toBe("Boston");
    });

    it("omits b when empty", () => {
      const params: CompareParams = { a: "Cambridge", b: "", radius: 0.5 };
      const sp = buildCompareSearchParams(params);
      expect(sp.get("a")).toBe("Cambridge");
      expect(sp.has("b")).toBe(false);
    });

    it("always includes radius", () => {
      const params: CompareParams = { a: "Cambridge", b: "Boston", radius: 2.5 };
      const sp = buildCompareSearchParams(params);
      expect(sp.get("radius")).toBe("2.5");
    });

    it("round-trips with parseCompareParams", () => {
      const original: CompareParams = { a: "Cambridge, MA", b: "Boston, MA", radius: 1.5 };
      const sp = buildCompareSearchParams(original);
      const parsed = parseCompareParams(sp);
      expect(parsed.params.a).toBe(original.a);
      expect(parsed.params.b).toBe(original.b);
      expect(parsed.params.radius).toBe(original.radius);
    });
  });

  describe("canFetchCompare", () => {
    it("returns true when both a and b have content", () => {
      expect(canFetchCompare({ a: "Cambridge", b: "Boston", radius: 0.5 })).toBe(true);
      expect(canFetchCompare({ a: "Cambridge, MA", b: "Boston, MA", radius: 1.0 })).toBe(true);
    });

    it("returns false when a is empty", () => {
      expect(canFetchCompare({ a: "", b: "Boston", radius: 0.5 })).toBe(false);
    });

    it("returns false when b is empty", () => {
      expect(canFetchCompare({ a: "Cambridge", b: "", radius: 0.5 })).toBe(false);
    });

    it("returns false when both are empty", () => {
      expect(canFetchCompare({ a: "", b: "", radius: 0.5 })).toBe(false);
    });

    it("returns false when a is whitespace only", () => {
      expect(canFetchCompare({ a: "   ", b: "Boston", radius: 0.5 })).toBe(false);
    });

    it("returns false when b is whitespace only", () => {
      expect(canFetchCompare({ a: "Cambridge", b: "\t\n", radius: 0.5 })).toBe(false);
    });

    it("returns true when both have content after trim", () => {
      expect(canFetchCompare({ a: "  Cambridge  ", b: "  Boston  ", radius: 0.5 })).toBe(true);
    });
  });
});
