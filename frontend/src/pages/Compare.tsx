/**
 * Compare page: two locations side-by-side with summary panels and neutral metric diffs (B vs A).
 * URL params: a, b, radius. Shareable compare links.
 *
 * Mobile (≤768px) shares the visual language of the Explore mobile layout:
 * sticky pill-style inputs at the top, a chip that opens a bottom-sheet
 * radius slider, and the comparison rendered as stacked cards below.
 */

import { useState } from "react";
import { nwiSummaryByQuery } from "../api/client";
import type { NwiSummaryResponse } from "../types/api";
import { CompareTable } from "../components/CompareTable";
import {
  parseCompareParams,
  buildCompareSearchParams,
  canFetchCompare,
  canonicalRadius,
  type CompareParams,
  COMPARE_PARAMS,
} from "../lib/compareParams";
import { useUrlDrivenSearch } from "../hooks/useUrlDrivenSearch";
import { useIsMobile } from "../hooks/useIsMobile";

const { MIN_RADIUS, MAX_RADIUS, STEP } = COMPARE_PARAMS;

export function Compare() {
  const isMobile = useIsMobile();
  const [radiusSheetOpen, setRadiusSheetOpen] = useState(false);
  const {
    params,
    result: bothSummaries,
    loading,
    error,
    validationMessage,
    updateDraft,
    submit,
  } = useUrlDrivenSearch<CompareParams, [NwiSummaryResponse, NwiSummaryResponse]>({
    parse: parseCompareParams,
    build: buildCompareSearchParams,
    canFetch: canFetchCompare,
    fetch: (p, signal) =>
      Promise.all([
        nwiSummaryByQuery(p.a, p.radius, { signal }),
        nwiSummaryByQuery(p.b, p.radius, { signal }),
      ]),
    emptyFetchMessage: "Enter both locations to compare.",
    trimParams: (p) => ({ ...p, a: p.a.trim(), b: p.b.trim() }),
  });

  const summaryA = bothSummaries?.[0] ?? null;
  const summaryB = bothSummaries?.[1] ?? null;

  function handleAChange(value: string) {
    updateDraft({
      a: value.slice(0, COMPARE_PARAMS.MAX_QUERY_LENGTH),
      b: params.b,
      radius: canonicalRadius(params.radius),
    });
  }

  function handleBChange(value: string) {
    updateDraft({
      a: params.a,
      b: value.slice(0, COMPARE_PARAMS.MAX_QUERY_LENGTH),
      radius: canonicalRadius(params.radius),
    });
  }

  function handleRadiusChange(value: number) {
    const r = canonicalRadius(value);
    updateDraft({ a: params.a, b: params.b, radius: r });
  }

  function handleCompare(e: React.FormEvent) {
    e.preventDefault();
    submit();
  }

  const showTable = summaryA && summaryB;

  if (isMobile) {
    return (
      <div className="compare compare--mobile">
        <div className="m-sticky-search">
          <form onSubmit={handleCompare}>
            <label htmlFor="compare-a-mobile" className="visually-hidden">
              Location A
            </label>
            <div className="m-search-row">
              <span className="m-search-icon" aria-hidden>A</span>
              <input
                id="compare-a-mobile"
                className="m-search-input"
                type="text"
                value={params.a}
                onChange={(e) => handleAChange(e.target.value)}
                placeholder="Location A (e.g. Cambridge, MA)"
                disabled={loading}
                autoComplete="off"
              />
            </div>
            <label htmlFor="compare-b-mobile" className="visually-hidden">
              Location B
            </label>
            <div className="m-search-row">
              <span className="m-search-icon" aria-hidden>B</span>
              <input
                id="compare-b-mobile"
                className="m-search-input"
                type="text"
                value={params.b}
                onChange={(e) => handleBChange(e.target.value)}
                placeholder="Location B (e.g. Somerville, MA)"
                disabled={loading}
                autoComplete="off"
              />
            </div>
            <div className="m-chip-row">
              <button
                type="button"
                className="m-chip"
                onClick={() => setRadiusSheetOpen(true)}
                aria-haspopup="dialog"
                aria-expanded={radiusSheetOpen}
              >
                Radius: {params.radius.toFixed(1)} mi
              </button>
              <button
                type="submit"
                className="m-search-go"
                disabled={loading}
              >
                {loading ? "…" : "Compare"}
              </button>
            </div>
          </form>
        </div>

        {(validationMessage || error) && (
          <div className="compare__error" role="alert">
            {validationMessage ?? error}
          </div>
        )}

        <div className="compare__mobile-body">
          {showTable ? (
            <CompareTable summaryA={summaryA} summaryB={summaryB} />
          ) : (
            <div className="compare-placeholder">
              {loading ? "Loading comparison..." : "Enter two locations and tap Compare to see the difference."}
            </div>
          )}
        </div>

        {radiusSheetOpen && (
          <>
            <div
              className="m-radius-scrim"
              onClick={() => setRadiusSheetOpen(false)}
              aria-hidden
            />
            <div className="m-radius-sheet" role="dialog" aria-label="Radius">
              <div className="m-radius-sheet-header">
                <span>Radius (miles): {params.radius.toFixed(1)}</span>
                <button
                  type="button"
                  className="m-radius-sheet-close"
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

  return (
    <div className="compare">
      <header className="compare__header">
        <h1>Compare</h1>
        <p className="compare__tagline">
          Compare two locations side-by-side. Metrics for B show the difference vs A (neutral). Uses EPA National Walkability Index scores within a configurable radius.
        </p>
      </header>

      <section className="compare__controls">
        <form onSubmit={handleCompare} className="compare__form">
          <div className="compare__input-group">
            <label htmlFor="compare-a">Location A</label>
            <input
              id="compare-a"
              type="text"
              value={params.a}
              onChange={(e) => handleAChange(e.target.value)}
              placeholder="e.g. Cambridge, MA"
              disabled={loading}
              autoComplete="off"
            />
          </div>
          <div className="compare__input-group">
            <label htmlFor="compare-b">Location B</label>
            <input
              id="compare-b"
              type="text"
              value={params.b}
              onChange={(e) => handleBChange(e.target.value)}
              placeholder="e.g. Somerville, MA"
              disabled={loading}
              autoComplete="off"
            />
          </div>
          <div className="compare__radius">
            <label htmlFor="compare-radius">Radius (miles): {params.radius.toFixed(1)}</label>
            <input
              id="compare-radius"
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
            {loading ? "Loading…" : "Compare"}
          </button>
        </form>
      </section>

      {(validationMessage || error) && (
        <div className="compare__error" role="alert">
          {validationMessage ?? error}
        </div>
      )}

      {showTable ? (
        <CompareTable summaryA={summaryA} summaryB={summaryB} />
      ) : (
        <div className="compare-placeholder">
            {loading ? "Loading comparison..." : "Enter two locations and click Compare to see the difference."}
        </div>
      )}
    </div>
  );
}
