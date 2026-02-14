/**
 * Compare page URL params: parse, build, validate, and constants.
 */

export interface CompareParams {
  a: string;
  b: string;
  radius: number;
}

export const COMPARE_PARAMS = {
  DEFAULT_RADIUS: 0.5,
  MIN_RADIUS: 0.1,
  MAX_RADIUS: 3,
  STEP: 0.1,
  MAX_QUERY_LENGTH: 200,
} as const;

/** Clamp and round radius to one decimal place within [MIN, MAX]. */
export function canonicalRadius(value: number): number {
  const clamped = Math.max(COMPARE_PARAMS.MIN_RADIUS, Math.min(COMPARE_PARAMS.MAX_RADIUS, value));
  return Math.round(clamped * 10) / 10;
}

export function parseCompareParams(
  searchParams: URLSearchParams,
): { params: CompareParams; validationError: string | null } {
  const a = searchParams.get("a") ?? "";
  const b = searchParams.get("b") ?? "";
  const rawRadius = searchParams.get("radius");

  if (rawRadius !== null && rawRadius !== "") {
    const parsed = Number(rawRadius);
    if (Number.isNaN(parsed)) {
      return {
        params: { a, b, radius: COMPARE_PARAMS.DEFAULT_RADIUS },
        validationError: "Radius must be a number.",
      };
    }
    return { params: { a, b, radius: canonicalRadius(parsed) }, validationError: null };
  }

  return { params: { a, b, radius: COMPARE_PARAMS.MIN_RADIUS }, validationError: null };
}

export function buildCompareSearchParams(params: CompareParams): URLSearchParams {
  const sp = new URLSearchParams();
  if (params.a) sp.set("a", params.a);
  if (params.b) sp.set("b", params.b);
  sp.set("radius", String(params.radius));
  return sp;
}

export function canFetchCompare(params: CompareParams): boolean {
  return params.a.trim().length > 0 && params.b.trim().length > 0;
}
