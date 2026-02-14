/**
 * Explore page URL params: parse, build, validate, and constants.
 */

import { RADIUS_DEFAULTS, canonicalRadius, parseRadius } from "./radiusParams";

export { canonicalRadius };

export type ExploreParams = { q: string; radius: number };

export const EXPLORE_PARAMS = RADIUS_DEFAULTS;

export function parseExploreParams(
  searchParams: URLSearchParams,
): { params: ExploreParams; validationError: string | null } {
  const q = searchParams.get("q") ?? "";
  const { radius, validationError } = parseRadius(searchParams.get("radius"));
  return { params: { q, radius }, validationError };
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
