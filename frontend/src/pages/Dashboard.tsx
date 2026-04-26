/**
 * Dashboard page: component analysis visualizations.
 * URL query params (q, radius) for shareability; reuses Explore params structure.
 *
 * Mobile (≤768px) uses the same visual language as the Explore mobile layout:
 * sticky pill-style search at the top, a chip that opens a bottom-sheet
 * radius slider, then summary cards / tabs / chart content stacked below.
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
import { useIsMobile } from "../hooks/useIsMobile";
import { COMPONENT_INFO, formatComponentLabel } from "../lib/componentLabels";
import { ComponentDistributionChart } from "../components/dashboard/ComponentDistributionChart";
import { ComponentCorrelationChart } from "../components/dashboard/ComponentCorrelationChart";
import { ComponentContributionChart } from "../components/dashboard/ComponentContributionChart";
import { NwiWasScatterChart } from "../components/dashboard/NwiWasScatterChart";
import { useMemo, useState, type ReactNode } from "react";

const { MIN_RADIUS, MAX_RADIUS, STEP } = EXPLORE_PARAMS;
type DashboardView = "overview" | "distribution" | "correlation" | "nwiWas";

function formatScore(value: number | null): string {
  return value == null ? "—" : value.toFixed(2);
}

export function Dashboard() {
  const isMobile = useIsMobile();
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
  const [activeView, setActiveView] = useState<DashboardView>("overview");
  const [radiusSheetOpen, setRadiusSheetOpen] = useState(false);

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
  const componentScores = useMemo(() => {
    if (!summary) {
      return [];
    }
    return [
      {
        key: "d2a_ranked",
        code: COMPONENT_INFO.d2a_ranked.code,
        label: COMPONENT_INFO.d2a_ranked.shortLabel,
        displayLabel: formatComponentLabel(COMPONENT_INFO.d2a_ranked),
        value: summary.components.employment_housing_mix_rank_mean,
      },
      {
        key: "d2b_ranked",
        code: COMPONENT_INFO.d2b_ranked.code,
        label: COMPONENT_INFO.d2b_ranked.shortLabel,
        displayLabel: formatComponentLabel(COMPONENT_INFO.d2b_ranked),
        value: summary.components.employment_type_diversity_rank_mean,
      },
      {
        key: "d3b_ranked",
        code: COMPONENT_INFO.d3b_ranked.code,
        label: COMPONENT_INFO.d3b_ranked.shortLabel,
        displayLabel: formatComponentLabel(COMPONENT_INFO.d3b_ranked),
        value: summary.components.intersection_density_rank_mean,
      },
      {
        key: "d4a_ranked",
        code: COMPONENT_INFO.d4a_ranked.code,
        label: COMPONENT_INFO.d4a_ranked.shortLabel,
        displayLabel: formatComponentLabel(COMPONENT_INFO.d4a_ranked),
        value: summary.components.transit_proximity_rank_mean_proxy,
      },
    ].filter((item) => item.value != null);
  }, [summary]);
  const strongestComponent = componentScores[0]
    ? [...componentScores].sort((a, b) => (b.value ?? 0) - (a.value ?? 0))[0]
    : null;
  const weakestComponent = componentScores[0]
    ? [...componentScores].sort((a, b) => (a.value ?? 0) - (b.value ?? 0))[0]
    : null;
  const hasComponentSummary = componentScores.length > 0;

  // Reusable content blocks --------------------------------------------------
  const summaryGrid: ReactNode = hasData && (
    <section className="dashboard__summary-grid" aria-label="Top-level dashboard insights">
      <article className="dashboard__summary-card">
        <h3>Average Score Across Block Groups</h3>
        <p className="dashboard__summary-value">{formatScore(summary.nwi.mean)}</p>
        <p className="dashboard__summary-hint">Scores range from 1–20. Higher = more walkable</p>
      </article>
      <article className="dashboard__summary-card">
        <h3>Block Groups within Radius</h3>
        <p className="dashboard__summary-value">{summary.counts.selected_block_groups}</p>
      </article>
      <article className="dashboard__summary-card">
        <h3>Strongest Component</h3>
        <p className="dashboard__summary-value dashboard__summary-value--component">
          {strongestComponent ? strongestComponent.displayLabel : "—"}
        </p>
        <p className="dashboard__summary-hint">
          {strongestComponent
            ? `Score: ${formatScore(strongestComponent.value)}`
            : "Not enough data to rank components."}
        </p>
      </article>
      <article className="dashboard__summary-card">
        <h3>Weakest Component</h3>
        <p className="dashboard__summary-value dashboard__summary-value--component">
          {weakestComponent ? weakestComponent.displayLabel : "—"}
        </p>
        <p className="dashboard__summary-hint">
          {weakestComponent
            ? `Score: ${formatScore(weakestComponent.value)}`
            : "Not enough data to rank components."}
        </p>
      </article>
    </section>
  );

  const tabs: ReactNode = hasData && (
    <div className="dashboard__tabs" role="tablist" aria-label="Dashboard analysis sections">
      <button
        type="button"
        role="tab"
        aria-selected={activeView === "overview"}
        className={`dashboard__tab ${activeView === "overview" ? "dashboard__tab--active" : ""}`}
        onClick={() => setActiveView("overview")}
      >
        Overview
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={activeView === "distribution"}
        className={`dashboard__tab ${activeView === "distribution" ? "dashboard__tab--active" : ""}`}
        onClick={() => setActiveView("distribution")}
      >
        Distribution
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={activeView === "correlation"}
        className={`dashboard__tab ${activeView === "correlation" ? "dashboard__tab--active" : ""}`}
        onClick={() => setActiveView("correlation")}
      >
        Correlation
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={activeView === "nwiWas"}
        className={`dashboard__tab ${activeView === "nwiWas" ? "dashboard__tab--active" : ""}`}
        onClick={() => setActiveView("nwiWas")}
      >
        Walkability vs Amenities
      </button>
    </div>
  );

  const sectionContent: ReactNode = (
    <>
      {hasData && activeView === "overview" && (
        <section className="dashboard__section" role="tabpanel" aria-label="Overview panel">
          <h2>Component Profile</h2>
          <p className="dashboard__section-description">
            Compare component averages with the overall NWI average to spot the strongest and weakest factors.
          </p>
          <ComponentContributionChart summary={summary} />
          <div className="dashboard__overview-notes">
            <h3>Quick read</h3>
            {hasComponentSummary && strongestComponent && weakestComponent ? (
              <ul>
                <li>
                  <strong>{strongestComponent.displayLabel}</strong> is currently the strongest dimension at{" "}
                  {formatScore(strongestComponent.value)}.
                </li>
                <li>
                  <strong>{weakestComponent.displayLabel}</strong> is the weakest dimension at{" "}
                  {formatScore(weakestComponent.value)}.
                </li>
                <li>
                  Use the Distribution and Correlation tabs to see how stable these patterns are across block
                  groups.
                </li>
              </ul>
            ) : (
              <p>Component summary is unavailable for this search.</p>
            )}
          </div>
        </section>
      )}

      {hasData && activeView === "distribution" && (
        <section className="dashboard__section" role="tabpanel" aria-label="Distribution panel">
          <h2>Component Distributions</h2>
          <p className="dashboard__section-description">
            How component scores (1 to 20) are distributed across block groups in this area.
          </p>
          <ComponentDistributionChart blockGroups={summary.block_groups} />
          <div className="dashboard__chart-help" aria-label="How to read component distributions">
            <h3>How to read this chart</h3>
            <ul>
              <li>
                <strong>X-axis:</strong> component score buckets from 1 to 20.
              </li>
              <li>
                <strong>Y-axis:</strong> number of block groups in each score bucket.
              </li>
              <li>
                <strong>Each color:</strong> one component, so you can compare shape and spread across components.
              </li>
              <li>
                <strong>Why it matters:</strong> this shows outliers and spread, not just the average.
              </li>
            </ul>
          </div>
        </section>
      )}

      {hasData && activeView === "correlation" && (
        <section className="dashboard__section" role="tabpanel" aria-label="Correlation panel">
          <h2>Component Correlations</h2>
          <p className="dashboard__section-description">
            Compare how each component moves with NWI in one view.
          </p>
          <ComponentCorrelationChart blockGroups={summary.block_groups} />
        </section>
      )}

      {hasData && activeView === "nwiWas" && (
        <section className="dashboard__section" role="tabpanel" aria-label="NWI versus WAS panel">
          <h2>Walkability vs Amenities</h2>
          <p className="dashboard__section-description">
            Compare the EPA National Walkability Index (NWI) with the Walkable Accessibility Score (WAS) to see where
            street form and nearby amenities tell the same or different stories.
          </p>
          <NwiWasScatterChart summary={summary} />
          <div className="dashboard__chart-help" aria-label="How to read NWI versus WAS">
            <h3>How to read this chart</h3>
            <ul>
              <li>
                <strong>Upper right:</strong> higher NWI and more reachable amenities.
              </li>
              <li>
                <strong>Lower right:</strong> Hollow Neighborhood candidates with walkable form but sparse amenities.
              </li>
              <li>
                <strong>Upper left:</strong> more amenities with lower NWI scores.
              </li>
              <li>
                <strong>Lower left:</strong> lower NWI and sparse destination access.
              </li>
            </ul>
          </div>
        </section>
      )}
    </>
  );

  const emptyState: ReactNode = !hasData && !loading && !error && !paramValidationMessage && (
    <div className="dashboard__empty">
      <p>Enter a location to view component analysis.</p>
      <p className="dashboard__empty-hint">
        You will see distributions, correlations, and contributions for the four NWI components:
        Employment &amp; Household Mix (D2A), Employment Mix (D2B), Intersection Density (D3B), and Transit
        Proximity (D4A), plus a WAS comparison when amenity data is available.
      </p>
    </div>
  );

  if (isMobile) {
    return (
      <div className="dashboard dashboard--mobile">
        <div className="m-sticky-search">
          <form onSubmit={handleSearch}>
            <label htmlFor="dashboard-search-mobile" className="visually-hidden">
              Address, ZIP, or city
            </label>
            <div className="m-search-row">
              <span className="m-search-icon" aria-hidden>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="7" />
                  <path d="m20 20-3.5-3.5" />
                </svg>
              </span>
              <input
                id="dashboard-search-mobile"
                className="m-search-input"
                type="text"
                value={params.q}
                onChange={(e) => handleQueryChange(e.target.value)}
                placeholder="e.g. Cambridge, MA"
                disabled={loading}
                autoComplete="off"
              />
              <button
                type="submit"
                className="m-search-go"
                disabled={loading}
              >
                {loading ? "…" : "Analyze"}
              </button>
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
            </div>
          </form>
        </div>

        {(paramValidationMessage || error) && (
          <div className="dashboard__error" role="alert">
            {paramValidationMessage ?? error}
          </div>
        )}

        <div className="dashboard__mobile-body">
          <header className="dashboard__header">
            <h1>Component Analysis</h1>
            <p className="dashboard__tagline">
              See which factors are shaping walkability, then explore the spread and relationships.
            </p>
          </header>

          {emptyState}
          {summaryGrid}
          {tabs}
          {sectionContent}
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
    <div className="dashboard">
      <header className="dashboard__header">
        <h1>Component Analysis Dashboard</h1>
        <p className="dashboard__tagline">
          See which factors are shaping walkability in a place, then explore the score spread and relationships.
        </p>
      </header>

      <div className="dashboard__workspace">
        <aside className="dashboard__sidebar">
          <section className="dashboard__controls">
            <form onSubmit={handleSearch} className="dashboard__form">
              <div className="dashboard__field dashboard__field--query">
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
              </div>
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
              <div className="dashboard__actions">
                <button type="submit" disabled={loading}>
                  {loading ? "Loading..." : "Analyze"}
                </button>
              </div>
            </form>
          </section>

          {(paramValidationMessage || error) && (
            <div className="dashboard__error" role="alert">
              {paramValidationMessage ?? error}
            </div>
          )}

          {summaryGrid}
        </aside>

        <section className="dashboard__content">
          {emptyState}
          {tabs}
          {sectionContent}
        </section>
      </div>
    </div>
  );
}
