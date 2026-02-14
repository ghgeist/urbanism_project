/**
 * API client for the Urbanism Walkability API.
 * Base URL is read from VITE_API_URL (defaults to local FastAPI).
 */

import type { GeocodeResponse, NwiSummaryResponse } from "../types/api";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function get<T>(path: string, params: Record<string, string | number | undefined> = {}): Promise<T> {
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") search.set(k, String(v));
  }
  const url = `${API_BASE}${path}${search.toString() ? `?${search}` : ""}`;
  const res = await fetch(url);
  const data = await res.json();
  if (!res.ok) {
    const err = data as { code?: string; message?: string };
    throw new Error(err.message ?? `API error ${res.status}`);
  }
  return data as T;
}

/** Resolve address/ZIP/city to coordinates. */
export async function geocode(q: string): Promise<GeocodeResponse> {
  return get<GeocodeResponse>("/geocode", { q });
}

/** Get NWI summary by location query (address, ZIP, or city). */
export async function nwiSummaryByQuery(
  q: string,
  selected_radius_miles: number,
  options?: {
    search_radius_miles?: number;
    min_delta?: number;
    top_n?: number;
  }
): Promise<NwiSummaryResponse> {
  return get<NwiSummaryResponse>("/nwi/summary/by-query", {
    q,
    selected_radius_miles,
    search_radius_miles: options?.search_radius_miles,
    min_delta: options?.min_delta ?? 2,
    top_n: options?.top_n ?? 3,
  });
}

/** Health check. */
export async function health(): Promise<{ status: string }> {
  return get<{ status: string }>("/health");
}
