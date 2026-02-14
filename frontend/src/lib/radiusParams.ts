/**
 * Shared radius constants and helpers used by both Explore and Compare param modules.
 */

export const RADIUS_DEFAULTS = {
  DEFAULT_RADIUS: 0.5,
  MIN_RADIUS: 0.1,
  MAX_RADIUS: 3,
  STEP: 0.1,
  MAX_QUERY_LENGTH: 200,
} as const;

/** Clamp and round radius to one decimal place within [MIN, MAX]. */
export function canonicalRadius(value: number): number {
  const clamped = Math.max(RADIUS_DEFAULTS.MIN_RADIUS, Math.min(RADIUS_DEFAULTS.MAX_RADIUS, value));
  return Math.round(clamped * 10) / 10;
}

/**
 * Parse a raw radius string from URL search params.
 * Returns the parsed radius and a validation error if the value is not a number.
 */
export function parseRadius(
  raw: string | null,
): { radius: number; validationError: string | null } {
  if (raw !== null && raw !== "") {
    const parsed = Number(raw);
    if (Number.isNaN(parsed)) {
      return { radius: RADIUS_DEFAULTS.DEFAULT_RADIUS, validationError: "Radius must be a number." };
    }
    return { radius: canonicalRadius(parsed), validationError: null };
  }
  return { radius: RADIUS_DEFAULTS.DEFAULT_RADIUS, validationError: null };
}
