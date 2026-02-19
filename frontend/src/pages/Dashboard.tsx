/**
 * Dashboard page: component analysis visualizations.
 * URL query params (q, radius) for shareability; reuses Explore params structure.
 */

import { nwiSummaryByQuery } from "../api/client";
import type { NwiSummaryResponse } from "../types/api";
import {
  EXPLORE_PARAMS,
  parseExploreParams,
  buildExploreSearchParams,
  canFetch,
  canonicalRadius,
  type ExploreParams,
} from "../lib/exploreParams";
import { useUrlDrivenSearch } from "../hooks/useUrlDrivenSearch";
import { ComponentDistributionChart } from "../components/dashboard/ComponentDistributionChart";
import { ComponentCorrelationChart } from "../components/dashboard/ComponentCorrelationChart";
import { ComponentContributionChart } from "../components/dashboard/ComponentContributionChart";
import { ComponentComparisonChart } from "../components/dashboard/ComponentComparisonChart";

const { MIN_RADIUS, MAX_RADIUS, STEP } = EXPLORE_PARAMS;

export function Dashboard() {
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
    emptyFetchMessage: "Enter a location to analyze components.",
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

  const hasData = summary && summary.block_groups.length > 0;

  return (
    <div className="dashboard">
      <header className="dashboard__header">
        <h1>Component Analysis Dashboard</h1>
        <p className="dashboard__tagline">
          Deep dive into the four components that make up the National Walkability Index.
        </p>
      </header>

      <div className="dashboard__body">
        <section className="dashboard__controls">
          <form onSubmit={handleSearch} className="dashboard__form">
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
            <div className="dashboard__radius">
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
              {loading ? "Loading…" : "Analyze"}
            </button>
          </form>
        </section>

        {(paramValidationMessage || error) && (
          <div className="dashboard__error" role="alert">
            {paramValidationMessage ?? error}
          </div>
        )}

        {!hasData && !loading && (
          <div className="dashboard__empty">
            <p>Enter a location to view component analysis.</p>
            <p className="dashboard__empty-hint">
              The dashboard shows distributions, correlations, and contributions of the four NWI components:
              Employment and Household Mix (D2A), Employment Mix (D2B), Street Intersection Density (D3B), and Proximity to Transit Stops (D4A).
            </p>
          </div>
        )}

        {hasData && (
          <div className="dashboard__visualizations">
            <section className="dashboard__section">
              <h2>Component Distributions</h2>
              <p className="dashboard__section-description">
                Distribution of component scores (1-20) across block groups in the selected area.
              </p>
              <ComponentDistributionChart blockGroups={summary.block_groups} />
            </section>

            <section className="dashboard__section">
              <h2>Component Correlations</h2>
              <p className="dashboard__section-description">
                How component scores relate to each other and to the overall NWI score.
              </p>
              <ComponentCorrelationChart blockGroups={summary.block_groups} />
            </section>

            <section className="dashboard__section">
              <h2>Component Contribution</h2>
              <p className="dashboard__section-description">
                Average component scores compared to the overall NWI mean. Components are ranked 1-20, where higher values indicate better walkability.
              </p>
              <ComponentContributionChart summary={summary} />
            </section>

            <section className="dashboard__section">
              <h2>Component Comparison</h2>
              <p className="dashboard__section-description">
                Side-by-side comparison of component means, showing which dimensions drive walkability in this area.
              </p>
              <ComponentComparisonChart summary={summary} />
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
