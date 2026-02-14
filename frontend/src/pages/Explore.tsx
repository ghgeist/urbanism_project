/**
 * Explore page: search input, radius slider, summary cards, map.
 * URL query params (q, radius) for shareability; replaceState while editing, pushState on submit.
 */

import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { nwiSummaryByQuery } from "../api/client";
import type { NwiSummaryResponse } from "../types/api";
import { SummaryCards } from "../components/SummaryCards";
import { MapView } from "../components/MapView";
import {
  EXPLORE_PARAMS,
  parseExploreParams,
  buildExploreSearchParams,
  canFetch,
  canonicalRadius,
  type ExploreParams,
} from "../lib/exploreParams";

const { MIN_RADIUS, MAX_RADIUS, STEP } = EXPLORE_PARAMS;

function getInitialParams(searchParams: URLSearchParams): ExploreParams {
  const { params } = parseExploreParams(searchParams);
  return params;
}

export function Explore() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initial = getInitialParams(searchParams);
  const [query, setQuery] = useState(initial.q);
  const [radius, setRadius] = useState(initial.radius);
  const [summary, setSummary] = useState<NwiSummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paramValidationMessage, setParamValidationMessage] = useState<string | null>(null);
  /** When true, we just called setSearchParams; skip state sync and fetch in the effect. */
  const weJustSetParamsRef = useRef(false);
  /** Tracks current search version to cancel stale async operations. */
  const searchVersionRef = useRef(0);

  /** Sync state from URL and optionally fetch (initial load or popstate). */
  useEffect(() => {
    const { params, validationError } = parseExploreParams(searchParams);

    // If we just set params programmatically, don't overwrite local state or re-fetch.
    if (weJustSetParamsRef.current) {
      weJustSetParamsRef.current = false;
      return;
    }

    // External URL change (initial load, browser back/forward): sync state from URL.
    setQuery(params.q);
    setRadius(params.radius);
    setParamValidationMessage(validationError);

    // Invalidate any in-flight handleSearch to prevent stale pushState.
    searchVersionRef.current += 1;

    if (validationError || !canFetch(params)) {
      // Reset loading in case we navigated away from an in-flight fetch.
      // The stale fetch's finally block won't run setLoading(false) due to version check.
      setLoading(false);
      return;
    }

    let cancelled = false;
    setError(null);
    setLoading(true);
    nwiSummaryByQuery(params.q, params.radius)
      .then((data) => {
        if (!cancelled) setSummary(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Request failed");
          setSummary(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [searchParams]);

  /** Update URL as draft (replaceState); no fetch. */
  function updateUrlDraft(next: ExploreParams) {
    weJustSetParamsRef.current = true;
    setSearchParams(buildExploreSearchParams(next), { replace: true });
  }

  function handleQueryChange(value: string) {
    const trimmed = value.slice(0, EXPLORE_PARAMS.MAX_QUERY_LENGTH);
    setQuery(trimmed);
    updateUrlDraft({
      q: trimmed.trim(),
      radius: canonicalRadius(radius),
    });
  }

  function handleRadiusChange(value: number) {
    const r = canonicalRadius(value);
    setRadius(r);
    updateUrlDraft({ q: query.trim(), radius: r });
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const params: ExploreParams = {
      q: query.trim(),
      radius: canonicalRadius(radius),
    };
    const { validationError } = parseExploreParams(
      new URLSearchParams({ q: params.q, radius: params.radius.toFixed(1) })
    );
    if (validationError) {
      setParamValidationMessage(validationError);
      return;
    }
    if (!canFetch(params)) {
      setParamValidationMessage("Enter a location to get a summary.");
      return;
    }
    setParamValidationMessage(null);
    setError(null);
    setLoading(true);

    // Capture version to detect if user navigated away during the async operation.
    const version = ++searchVersionRef.current;

    try {
      const data = await nwiSummaryByQuery(params.q, params.radius);
      // If user navigated (back/forward) during fetch, version will have changed; abort.
      if (searchVersionRef.current !== version) return;
      setSummary(data);
      weJustSetParamsRef.current = true;
      setSearchParams(buildExploreSearchParams(params), { replace: false });
    } catch (err) {
      if (searchVersionRef.current !== version) return;
      setError(err instanceof Error ? err.message : "Request failed");
      setSummary(null);
    } finally {
      if (searchVersionRef.current === version) {
        setLoading(false);
      }
    }
  }

  return (
    <div className="explore">
      <header className="explore__header">
        <h1>Explore</h1>
        <p className="explore__tagline">
          See how everyday convenience and transit viability vary around an address or area.
        </p>
      </header>

      <div className="explore__body">
        <div className="explore__left">
          <section className="explore__controls">
            <form onSubmit={handleSearch} className="explore__form">
              <label htmlFor="search">Address, ZIP, or city</label>
              <input
                id="search"
                type="text"
                value={query}
                onChange={(e) => handleQueryChange(e.target.value)}
                placeholder="e.g. Cambridge, MA"
                disabled={loading}
                autoComplete="off"
              />
              <div className="explore__radius">
                <label htmlFor="radius">Radius (miles): {radius.toFixed(1)}</label>
                <input
                  id="radius"
                  type="range"
                  min={MIN_RADIUS}
                  max={MAX_RADIUS}
                  step={STEP}
                  value={radius}
                  onChange={(e) => handleRadiusChange(Number(e.target.value))}
                  disabled={loading}
                />
              </div>
              <button type="submit" disabled={loading}>
                {loading ? "Loading…" : "Get summary"}
              </button>
            </form>
          </section>

          {(paramValidationMessage || error) && (
            <div className="explore__error" role="alert">
              {paramValidationMessage ?? error}
            </div>
          )}

          {summary && (
            <>
              <SummaryCards summary={summary} />
              {summary.walkable_island?.is_island && (
                <div className="explore__island">
                  Walkable Island: high local NWI with lower surrounding context.
                </div>
              )}
              {summary.upgrade_potential?.found &&
                summary.upgrade_potential.candidates?.length > 0 && (
                  <section className="explore__nearby">
                    <h2>Nearby-better candidates</h2>
                    <table>
                      <thead>
                        <tr>
                          <th>Block Group ID</th>
                          <th>NWI Score</th>
                          <th>NWI Improvement</th>
                          <th>Distance (mi)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {summary.upgrade_potential.candidates.map((c, i) => (
                          <tr key={c.geoid20 ?? i}>
                            <td>{c.geoid20 ?? "—"}</td>
                            <td>{c.natwalkind != null ? c.natwalkind.toFixed(2) : "—"}</td>
                            <td>{c.delta_nwi != null ? `+${c.delta_nwi.toFixed(2)}` : "—"}</td>
                            <td>{c.dist_miles != null ? c.dist_miles.toFixed(2) : "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </section>
                )}
            </>
          )}
        </div>

        <aside className="explore__right" aria-label="Spatial context">
          {summary ? (
            <div className="explore__map explore__map--split">
              <MapView
                lat={summary.origin.lat}
                lon={summary.origin.lon}
                radiusMiles={summary.selected_radius_miles}
                label={summary.origin.label ?? undefined}
                fillHeight
              />
            </div>
          ) : (
            <p className="explore__map-placeholder">
              Enter a location to view spatial context.
            </p>
          )}
        </aside>
      </div>
    </div>
  );
}
