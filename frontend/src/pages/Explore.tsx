/**
 * Explore page: search input, radius slider, summary cards, map.
 * URL query params (q, radius) for shareability; replaceState while editing, pushState on submit.
 */

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
import { useUrlDrivenSearch } from "../hooks/useUrlDrivenSearch";
import { useEffect, useRef, useState } from "react";

const { MIN_RADIUS, MAX_RADIUS, STEP } = EXPLORE_PARAMS;
const WRIGLEY_FIELD_LAT = 41.9484;
const WRIGLEY_FIELD_LON = -87.6553;
const WRIGLEY_FIELD_ADDRESS = "1060 W Addison St, Chicago, IL 60613";
const WRIGLEY_FIELD_PLACEHOLDER = "1060 W Addison St, Chicago";
const DEFAULT_PRELOAD_RETRY_DELAY_MS = 1000;
const MAX_DEFAULT_PRELOAD_RETRIES = 1;

export function Explore() {
  const [defaultSummary, setDefaultSummary] = useState<NwiSummaryResponse | null>(null);
  const [preloadRetryTick, setPreloadRetryTick] = useState(0);
  const preloadStatusRef = useRef<"idle" | "loading" | "success">("idle");
  const preloadRetryCountRef = useRef(0);
  const preloadRetryTimerRef = useRef<number | null>(null);
  const {
    params,
    result: summary,
    loading,
    error,
    validationMessage: paramValidationMessage,
    updateDraft,
    submit,
  } = useUrlDrivenSearch<ExploreParams, NwiSummaryResponse>({
    parse: parseExploreParams,
    build: buildExploreSearchParams,
    canFetch,
    fetch: (p, signal) => nwiSummaryByQuery(p.q, p.radius, { signal }),
    emptyFetchMessage: "Enter a location to get a summary.",
    trimParams: (p) => ({ ...p, q: p.q.trim() }),
  });
  const initialPreloadRadiusRef = useRef(params.radius);

  useEffect(() => {
    // Preload default map overlays without refetching on radius slider edits.
    if (summary || params.q.trim() !== "") return;
    if (preloadStatusRef.current === "loading" || preloadStatusRef.current === "success") return;

    preloadStatusRef.current = "loading";
    const preloadRadius = initialPreloadRadiusRef.current;
    const controller = new AbortController();
    let ignore = false;
    nwiSummaryByQuery(WRIGLEY_FIELD_ADDRESS, preloadRadius, { signal: controller.signal })
      .then((res) => {
        if (ignore) return;
        setDefaultSummary(res);
        preloadStatusRef.current = "success";
      })
      .catch((err: unknown) => {
        if (ignore) return;
        preloadStatusRef.current = "idle";
        if (err instanceof DOMException && err.name === "AbortError") return;
        setDefaultSummary(null);
        if (
          preloadRetryCountRef.current < MAX_DEFAULT_PRELOAD_RETRIES &&
          preloadRetryTimerRef.current === null
        ) {
          preloadRetryCountRef.current += 1;
          preloadRetryTimerRef.current = window.setTimeout(() => {
            preloadRetryTimerRef.current = null;
            setPreloadRetryTick((n) => n + 1);
          }, DEFAULT_PRELOAD_RETRY_DELAY_MS);
        }
      });

    return () => {
      ignore = true;
      if (preloadStatusRef.current === "loading") {
        preloadStatusRef.current = "idle";
      }
      controller.abort();
    };
  }, [summary, params.q, preloadRetryTick]);

  useEffect(() => {
    return () => {
      if (preloadRetryTimerRef.current !== null) {
        window.clearTimeout(preloadRetryTimerRef.current);
      }
    };
  }, []);

  const mapSummary = summary ?? (params.q.trim() === "" ? defaultSummary : null);

  function handleQueryChange(value: string) {
    updateDraft({
      q: value.slice(0, EXPLORE_PARAMS.MAX_QUERY_LENGTH),
      radius: canonicalRadius(params.radius),
    });
  }

  function handleRadiusChange(value: number) {
    const r = canonicalRadius(value);
    updateDraft({ q: params.q, radius: r });
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    submit();
  }

  return (
    <div className="explore">
      <header className="explore__header">
        <h1>Explore</h1>
        <p className="explore__tagline">
          Explore walkability scores from the EPA National Walkability Index around any U.S. address or area.
        </p>
      </header>

      <div className="explore__body">
        <div className="explore__left">
          <section className="explore__controls">
            <form onSubmit={handleSearch} className="explore__form">
              <div className="explore__input-group">
                <label htmlFor="search">Address, ZIP, or city</label>
                <input
                  id="search"
                  type="text"
                  value={params.q}
                  onChange={(e) => handleQueryChange(e.target.value)}
                  placeholder={WRIGLEY_FIELD_PLACEHOLDER}
                  disabled={loading}
                  autoComplete="off"
                />
              </div>
              <div className="explore__radius">
                <label htmlFor="radius">Radius (miles): {params.radius.toFixed(1)}</label>
                <input
                  id="radius"
                  type="range"
                  min={MIN_RADIUS}
                  max={MAX_RADIUS}
                  step={STEP}
                  value={params.radius}
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
                  <strong>Walkable Island:</strong> This area has a high NWI score (≥15.26) but is surrounded by block groups with lower scores (mean NWI ≤10.51). This may indicate an isolated walkable area rather than a walkable neighborhood.
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
          <div className="explore__map explore__map--split">
            <MapView
              lat={mapSummary?.origin.lat ?? WRIGLEY_FIELD_LAT}
              lon={mapSummary?.origin.lon ?? WRIGLEY_FIELD_LON}
              radiusMiles={mapSummary?.selected_radius_miles ?? params.radius}
              label={mapSummary?.origin.label ?? WRIGLEY_FIELD_ADDRESS}
              blockGroups={mapSummary?.block_groups}
              nwiMean={mapSummary?.nwi.mean}
              fillHeight
            />
          </div>
        </aside>
      </div>
    </div>
  );
}
