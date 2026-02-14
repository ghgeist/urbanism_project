/**
 * Explore page: search input, radius slider, summary cards, map.
 * State is intended to live in URL query params for shareability (Phase 1: local state).
 */

import { useState } from "react";
import { nwiSummaryByQuery } from "../api/client";
import type { NwiSummaryResponse } from "../types/api";
import { SummaryCards } from "../components/SummaryCards";
import { MapView } from "../components/MapView";

const DEFAULT_RADIUS = 0.5;
const MIN_RADIUS = 0.1;
const MAX_RADIUS = 3;
const STEP = 0.1;

export function Explore() {
  const [query, setQuery] = useState("");
  const [radius, setRadius] = useState(DEFAULT_RADIUS);
  const [summary, setSummary] = useState<NwiSummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    setError(null);
    setLoading(true);
    try {
      const data = await nwiSummaryByQuery(q, radius);
      setSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
      setSummary(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="explore">
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
                onChange={(e) => setQuery(e.target.value)}
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
                  onChange={(e) => setRadius(Number(e.target.value))}
                  disabled={loading}
                />
              </div>
              <button type="submit" disabled={loading}>
                {loading ? "Loading…" : "Get summary"}
              </button>
            </form>
          </section>

          {error && (
            <div className="explore__error" role="alert">
              {error}
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
    </main>
  );
}
