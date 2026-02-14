/**
 * Explore page URL params: parse, build, validate, and constants.
 */

export interface ExploreParams {
  q: string;
  radius: number;
}

export const EXPLORE_PARAMS = {
  DEFAULT_RADIUS: 0.5,
  MIN_RADIUS: 0.1,
  MAX_RADIUS: 3,
  STEP: 0.1,
  MAX_QUERY_LENGTH: 200,
} as const;

/** Clamp and round radius to one decimal place within [MIN, MAX]. */
export function canonicalRadius(value: number): number {
  const clamped = Math.max(EXPLORE_PARAMS.MIN_RADIUS, Math.min(EXPLORE_PARAMS.MAX_RADIUS, value));
  return Math.round(clamped * 10) / 10;
}

export function parseExploreParams(
  searchParams: URLSearchParams,
): { params: ExploreParams; validationError: string | null } {
  const q = searchParams.get("q") ?? "";
  const rawRadius = searchParams.get("radius");

  if (rawRadius !== null && rawRadius !== "") {
    const parsed = Number(rawRadius);
    if (Number.isNaN(parsed)) {
      return {
        params: { q, radius: EXPLORE_PARAMS.DEFAULT_RADIUS },
        validationError: "Radius must be a number.",
      };
    }
    return { params: { q, radius: canonicalRadius(parsed) }, validationError: null };
  }

  return { params: { q, radius: EXPLORE_PARAMS.MIN_RADIUS }, validationError: null };
}

export function buildExploreSearchParams(params: ExploreParams): URLSearchParams {
  const sp = new URLSearchParams();
  if (params.q) sp.set("q", params.q);
  sp.set("radius", String(params.radius));
  return sp;
}

export function canFetch(params: ExploreParams): boolean {
  return params.q.trim().length > 0;
}
