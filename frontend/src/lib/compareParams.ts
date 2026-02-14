/**
 * Compare page URL params: parse, build, validate, and constants.
 */

import { RADIUS_DEFAULTS, canonicalRadius, parseRadius } from "./radiusParams";

export { canonicalRadius };

export type CompareParams = { a: string; b: string; radius: number };

export const COMPARE_PARAMS = RADIUS_DEFAULTS;

export function parseCompareParams(
  searchParams: URLSearchParams,
): { params: CompareParams; validationError: string | null } {
  const a = searchParams.get("a") ?? "";
  const b = searchParams.get("b") ?? "";
  const { radius, validationError } = parseRadius(searchParams.get("radius"));
  return { params: { a, b, radius }, validationError };
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
