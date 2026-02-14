/**
 * API client for the Urbanism Walkability API.
 * Base URL: VITE_API_URL at build time. When unset in the browser, uses same origin
 * so Vite's dev proxy ( /health, /geocode, /nwi → backend) avoids CORS.
 */

import type { ErrorResponse, GeocodeResponse, NwiSummaryResponse } from "../types/api";

function getApiBase(): string {
  const env = import.meta.env.VITE_API_URL;
  if (env) return env;
  if (import.meta.env.MODE === "test") return "http://127.0.0.1:8000";
  if (typeof window !== "undefined") return "";
  return "http://127.0.0.1:8000";
}

/** User-facing messages for API error codes. Canonical codes documented in api/schemas.py ErrorResponse. */
const API_ERROR_MESSAGES: Record<string, string> = {
  location_not_found: "Location not found. Try a city name or ZIP code.",
  invalid_request: "Invalid request. Check your input and try again.",
  validation_error: "Invalid parameters. Check your input and try again.",
  internal_error: "Something went wrong. Please try again later.",
  http_404: "Location not found. Try a city name or ZIP code.",
  http_422: "Invalid parameters. Check your input and try again.",
};

async function get<T>(
  path: string,
  params: Record<string, string | number | undefined> = {},
  signal?: AbortSignal,
): Promise<T> {
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") search.set(k, String(v));
  }
  const url = `${getApiBase()}${path}${search.toString() ? `?${search}` : ""}`;
  const res = await fetch(url, signal ? { signal } : undefined);
  const text = await res.text();
  let data: unknown;
  try {
    data = text ? JSON.parse(text) : undefined;
  } catch {
    data = undefined;
  }
  if (!res.ok) {
    const err = data as ErrorResponse | undefined;
    const code = err?.code;
    const userMessage =
      (code && API_ERROR_MESSAGES[code]) ?? err?.message ?? `Request failed (${res.status}).`;
    throw new Error(userMessage);
  }
  if (data === undefined) {
    throw new Error(`Invalid response (${res.status})`);
  }
  return data as T;
}

/** Resolve address/ZIP/city to coordinates. */
export async function geocode(q: string, signal?: AbortSignal): Promise<GeocodeResponse> {
  return get<GeocodeResponse>("/geocode", { q }, signal);
}

/** Get NWI summary by location query (address, ZIP, or city). */
export async function nwiSummaryByQuery(
  q: string,
  selected_radius_miles: number,
  options?: {
    search_radius_miles?: number;
    min_delta?: number;
    top_n?: number;
    signal?: AbortSignal;
  }
): Promise<NwiSummaryResponse> {
  return get<NwiSummaryResponse>("/nwi/summary/by-query", {
    q,
    selected_radius_miles,
    search_radius_miles: options?.search_radius_miles,
    min_delta: options?.min_delta ?? 2,
    top_n: options?.top_n ?? 3,
  }, options?.signal);
}

/** Health check. */
export async function health(): Promise<{ status: string }> {
  return get<{ status: string }>("/health");
}
