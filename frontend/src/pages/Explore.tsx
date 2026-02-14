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

const { MIN_RADIUS, MAX_RADIUS, STEP } = EXPLORE_PARAMS;

export function Explore() {
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
                value={params.q}
                onChange={(e) => handleQueryChange(e.target.value)}
                placeholder="e.g. Cambridge, MA"
                disabled={loading}
                autoComplete="off"
              />
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
