/**
 * Explore page: search input, radius slider, summary cards, map.
 * URL query params (q, radius) for shareability; replaceState while editing, pushState on submit.
 *
 * Two layouts share most of the logic:
 *  - Desktop / tablet: existing two-column split (controls + cards on the left,
 *    sticky map on the right).
 *  - Mobile (≤768px): map-first. A sticky search bar sits at the top with an
 *    inline radius chip + go button; the map fills the screen behind a
 *    draggable bottom sheet that holds the cards, callouts, and table. A
 *    "Search this area" pill appears when the user pans the map.
 */

import { nwiSummaryByQuery } from "../api/client";
import type { NwiSummaryResponse } from "../types/api";
import { SummaryCards } from "../components/SummaryCards";
import { MapView } from "../components/MapView";
import { MobileBottomSheet } from "../components/MobileBottomSheet";
import {
  EXPLORE_PARAMS,
  parseExploreParams,
  buildExploreSearchParams,
  canFetch,
  canonicalRadius,
  type ExploreParams,
} from "../lib/exploreParams";
import { useUrlDrivenSearch } from "../hooks/useUrlDrivenSearch";
import { useIsMobile } from "../hooks/useIsMobile";
import { useEffect, useRef, useState, type ReactNode } from "react";

const { MIN_RADIUS, MAX_RADIUS, STEP } = EXPLORE_PARAMS;
const WRIGLEY_FIELD_LAT = 41.9484;
const WRIGLEY_FIELD_LON = -87.6553;
const WRIGLEY_FIELD_ADDRESS = "1060 W Addison St, Chicago, IL 60613";
const WRIGLEY_FIELD_PLACEHOLDER = "1060 W Addison St, Chicago";
const DEFAULT_PRELOAD_RETRY_DELAY_MS = 1000;
const MAX_DEFAULT_PRELOAD_RETRIES = 1;

/** Distance (miles, very rough) below which the map center is considered
 *  unchanged. ~0.05 mi ≈ 80 m, well within map jitter from a pinch-zoom. */
const SEARCH_AREA_THRESHOLD_DEG = 0.001;

export function Explore() {
  const isMobile = useIsMobile();
  const [defaultSummary, setDefaultSummary] = useState<NwiSummaryResponse | null>(null);
  /** Drives the subtle elevation under the sticky search row. The shadow
   *  only appears once the user has scrolled past a small threshold so the
   *  bar sits flush at the very top of the page. */
  const [pageScrolled, setPageScrolled] = useState(false);
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
  const [radiusSheetOpen, setRadiusSheetOpen] = useState(false);
  const [pendingMapCenter, setPendingMapCenter] = useState<{ lat: number; lon: number } | null>(null);

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

  // Clear any "Search this area" suggestion whenever the queried location
  // changes (e.g. user submitted a new address).
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- New query origin invalidates any pending recenter suggestion.
    setPendingMapCenter(null);
  }, [summary?.origin.lat, summary?.origin.lon]);

  // Track page scroll for the sticky search shadow (mobile only — listener
  // is cheap, and the class is only consumed by mobile CSS).
  useEffect(() => {
    if (!isMobile) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- Ensure stale mobile scroll shadow state is reset when switching layouts.
      setPageScrolled(false);
      return;
    }
    const SCROLL_SHADOW_THRESHOLD = 4;
    function onScroll() {
      setPageScrolled(window.scrollY > SCROLL_SHADOW_THRESHOLD);
    }
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [isMobile]);

  const mapSummary = summary ?? (params.q.trim() === "" ? defaultSummary : null);
  const mapLat = mapSummary?.origin.lat ?? WRIGLEY_FIELD_LAT;
  const mapLon = mapSummary?.origin.lon ?? WRIGLEY_FIELD_LON;

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

  function handleMapCenterChanged(lat: number, lon: number) {
    const dLat = Math.abs(lat - mapLat);
    const dLon = Math.abs(lon - mapLon);
    if (dLat < SEARCH_AREA_THRESHOLD_DEG && dLon < SEARCH_AREA_THRESHOLD_DEG) {
      setPendingMapCenter(null);
    } else {
      setPendingMapCenter({ lat, lon });
    }
  }

  function searchPendingArea() {
    if (!pendingMapCenter) return;
    // Backend geocoder accepts "lat, lon" strings; submit as a fresh query.
    const coordQuery = `${pendingMapCenter.lat.toFixed(5)}, ${pendingMapCenter.lon.toFixed(5)}`;
    const next = { q: coordQuery, radius: canonicalRadius(params.radius) };
    setPendingMapCenter(null);
    updateDraft(next);
    // Pass the fresh params explicitly so submit doesn't see stale state
    // from its own captured closure.
    submit(next);
  }

  // Shared form pieces -------------------------------------------------------
  const searchAreaButton = pendingMapCenter ? (
    <button
      type="button"
      className="map-view__search-area"
      onClick={searchPendingArea}
      disabled={loading}
    >
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="M21 12a9 9 0 1 1-3-6.7" />
        <path d="M21 4v5h-5" />
      </svg>
      Search this area
    </button>
  ) : null;

  const resultsContent: ReactNode = (
    <>
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
          {summary.hollow_neighborhood?.is_hollow && (
            <div className="explore__hollow" role="note">
              <strong>Hollow Neighborhood:</strong> The area has walkable street design (mean NWI ≥
              {summary.hollow_neighborhood.nwi_threshold.toFixed(1)}) but few nearby
              destinations (mean WAS ≤
              {summary.hollow_neighborhood.was_threshold.toFixed(1)}). Good bones,
              missing amenities — a candidate for infill retail/services rather than
              street redesign.
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
    </>
  );

  // Mobile layout ------------------------------------------------------------
  if (isMobile) {
    return (
      <div className="explore explore--mobile">
        <div className={`explore__sticky-search ${pageScrolled ? "explore__sticky-search--scrolled" : ""}`}>
          <form onSubmit={handleSearch} className="explore__search-row">
            <label htmlFor="search-mobile" className="visually-hidden">
              Address, ZIP, or city
            </label>
            <span className="explore__search-icon" aria-hidden>
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3.5-3.5" />
              </svg>
            </span>
            <input
              id="search-mobile"
              type="text"
              value={params.q}
              onChange={(e) => handleQueryChange(e.target.value)}
              placeholder={WRIGLEY_FIELD_PLACEHOLDER}
              disabled={loading}
              autoComplete="off"
              className="explore__search-input"
            />
            <button
              type="submit"
              className="explore__search-go"
              disabled={loading}
              aria-label="Search this address"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3.5-3.5" />
              </svg>
              <span>{loading ? "…" : "Search"}</span>
            </button>
          </form>
          <div className="explore__chip-row">
            <button
              type="button"
              className="explore__chip"
              onClick={() => setRadiusSheetOpen(true)}
              aria-haspopup="dialog"
              aria-expanded={radiusSheetOpen}
            >
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <circle cx="12" cy="12" r="9" />
                <circle cx="12" cy="12" r="3" />
              </svg>
              Radius: {params.radius.toFixed(1)} mi
            </button>
          </div>
        </div>

        <div className="explore__map-stage">
          <MapView
            lat={mapLat}
            lon={mapLon}
            radiusMiles={mapSummary?.selected_radius_miles ?? params.radius}
            label={mapSummary?.origin.label ?? WRIGLEY_FIELD_ADDRESS}
            blockGroups={mapSummary?.block_groups}
            nwiMean={mapSummary?.nwi.mean}
            fillHeight
            hideChrome
            onCenterChanged={handleMapCenterChanged}
            overlay={searchAreaButton}
          />
        </div>

        <MobileBottomSheet initialSnap={summary ? "half" : "peek"}>
          <div className="explore__sheet-header">
            <h1>Explore</h1>
            <p className="explore__tagline">
              EPA National Walkability Index around any U.S. address.
            </p>
          </div>
          {resultsContent}
        </MobileBottomSheet>

        {radiusSheetOpen && (
          <>
            <div
              className="explore__radius-scrim"
              onClick={() => setRadiusSheetOpen(false)}
              aria-hidden
            />
            <div className="explore__radius-sheet" role="dialog" aria-label="Radius">
              <div className="explore__radius-sheet-header">
                <span>Radius (miles): {params.radius.toFixed(1)}</span>
                <button
                  type="button"
                  className="explore__radius-sheet-close"
                  onClick={() => setRadiusSheetOpen(false)}
                  aria-label="Close radius selector"
                >
                  Done
                </button>
              </div>
              <input
                aria-label="Radius slider"
                type="range"
                min={MIN_RADIUS}
                max={MAX_RADIUS}
                step={STEP}
                value={params.radius}
                onChange={(e) => handleRadiusChange(Number(e.target.value))}
              />
            </div>
          </>
        )}
      </div>
    );
  }

  // Desktop / tablet layout (unchanged) -------------------------------------
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
          {resultsContent}
        </div>

        <aside className="explore__right" aria-label="Spatial context">
          <div className="explore__map explore__map--split">
            <MapView
              lat={mapLat}
              lon={mapLon}
              radiusMiles={mapSummary?.selected_radius_miles ?? params.radius}
              label={mapSummary?.origin.label ?? WRIGLEY_FIELD_ADDRESS}
              blockGroups={mapSummary?.block_groups}
              nwiMean={mapSummary?.nwi.mean}
              onCenterChanged={handleMapCenterChanged}
              overlay={searchAreaButton}
              fillHeight
            />
          </div>
        </aside>
      </div>
    </div>
  );
}
