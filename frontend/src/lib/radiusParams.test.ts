import { describe, expect, it } from "vitest";
import { RADIUS_DEFAULTS, canonicalRadius, parseRadius } from "./radiusParams";

describe("radiusParams", () => {
  describe("RADIUS_DEFAULTS", () => {
    it("has expected constant values", () => {
      expect(RADIUS_DEFAULTS.DEFAULT_RADIUS).toBe(0.5);
      expect(RADIUS_DEFAULTS.MIN_RADIUS).toBe(0.1);
      expect(RADIUS_DEFAULTS.MAX_RADIUS).toBe(3);
      expect(RADIUS_DEFAULTS.STEP).toBe(0.1);
      expect(RADIUS_DEFAULTS.MAX_QUERY_LENGTH).toBe(200);
    });
  });

  describe("canonicalRadius", () => {
    it("returns value unchanged when within bounds", () => {
      expect(canonicalRadius(0.5)).toBe(0.5);
      expect(canonicalRadius(1.0)).toBe(1.0);
      expect(canonicalRadius(2.5)).toBe(2.5);
    });

    it("clamps values below MIN_RADIUS to MIN_RADIUS", () => {
      expect(canonicalRadius(0.0)).toBe(0.1);
      expect(canonicalRadius(-1.0)).toBe(0.1);
      expect(canonicalRadius(0.05)).toBe(0.1);
    });

    it("clamps values above MAX_RADIUS to MAX_RADIUS", () => {
      expect(canonicalRadius(3.0)).toBe(3.0);
      expect(canonicalRadius(5.0)).toBe(3.0);
      expect(canonicalRadius(10.0)).toBe(3.0);
    });

    it("rounds to one decimal place", () => {
      expect(canonicalRadius(1.23)).toBe(1.2);
      expect(canonicalRadius(1.26)).toBe(1.3);
      // JavaScript Math.round rounds to nearest integer, so 1.25 * 10 = 12.5 rounds to 13, then / 10 = 1.3
      expect(canonicalRadius(1.25)).toBe(1.3);
      expect(canonicalRadius(0.15)).toBe(0.2);
    });

    it("handles edge cases", () => {
      expect(canonicalRadius(0.1)).toBe(0.1);
      expect(canonicalRadius(3.0)).toBe(3.0);
      expect(canonicalRadius(1.99)).toBe(2.0);
    });
  });

  describe("parseRadius", () => {
    it("returns DEFAULT_RADIUS when input is null", () => {
      const result = parseRadius(null);
      expect(result.radius).toBe(RADIUS_DEFAULTS.DEFAULT_RADIUS);
      expect(result.validationError).toBeNull();
    });

    it("returns DEFAULT_RADIUS when input is empty string", () => {
      const result = parseRadius("");
      expect(result.radius).toBe(RADIUS_DEFAULTS.DEFAULT_RADIUS);
      expect(result.validationError).toBeNull();
    });

    it("parses valid numeric strings", () => {
      expect(parseRadius("1.0")).toEqual({ radius: 1.0, validationError: null });
      expect(parseRadius("0.5")).toEqual({ radius: 0.5, validationError: null });
      expect(parseRadius("2.5")).toEqual({ radius: 2.5, validationError: null });
    });

    it("clamps parsed values to valid range", () => {
      expect(parseRadius("0.0")).toEqual({ radius: 0.1, validationError: null });
      expect(parseRadius("5.0")).toEqual({ radius: 3.0, validationError: null });
      expect(parseRadius("-1.0")).toEqual({ radius: 0.1, validationError: null });
    });

    it("rounds parsed values to one decimal place", () => {
      expect(parseRadius("1.23")).toEqual({ radius: 1.2, validationError: null });
      expect(parseRadius("1.26")).toEqual({ radius: 1.3, validationError: null });
    });

    it("returns validation error for non-numeric strings", () => {
      const result = parseRadius("not a number");
      expect(result.radius).toBe(RADIUS_DEFAULTS.DEFAULT_RADIUS);
      expect(result.validationError).toBe("Radius must be a number.");
    });

    it("returns validation error for NaN", () => {
      const result = parseRadius("NaN");
      expect(result.radius).toBe(RADIUS_DEFAULTS.DEFAULT_RADIUS);
      expect(result.validationError).toBe("Radius must be a number.");
    });

    it("handles whitespace-only strings", () => {
      // Number("   ") returns 0, which is then clamped to MIN_RADIUS (0.1)
      const result = parseRadius("   ");
      expect(result.radius).toBe(RADIUS_DEFAULTS.MIN_RADIUS);
      expect(result.validationError).toBeNull();
    });
  });
});
