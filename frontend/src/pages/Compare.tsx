/**
 * Compare page: two locations side-by-side with summary panels and neutral metric diffs (B vs A).
 * URL params: a, b, radius. Shareable compare links.
 */

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

const { MIN_RADIUS, MAX_RADIUS, STEP } = COMPARE_PARAMS;

export function Compare() {
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
