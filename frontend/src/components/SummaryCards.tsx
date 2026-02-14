/**
 * Four summary cards: Everyday Convenience, Transit Viability, Variation, Upgrade Potential.
 * Neutral descriptors only; no moral color coding per product plan.
 * Optional diffFrom: when set (e.g. Compare page B panel), show neutral delta vs baseline.
 */

import type { NwiSummaryResponse } from "../types/api";

function formatMetric(value: number | null | undefined): string {
  if (value == null) return "—";
  return value.toFixed(2);
}

/** Format neutral delta for Compare view: "+0.5 vs A" or "0.3 lower than A". */
function formatDelta(
  value: number | null | undefined,
  baseline: number | null | undefined,
  label = "first"
): string | null {
  if (value == null || baseline == null || !Number.isFinite(value) || !Number.isFinite(baseline))
    return null;
  const delta = value - baseline;
  if (Math.abs(delta) < 0.01) return `same as ${label}`;
  if (delta > 0) return `+${delta.toFixed(2)} vs ${label}`;
  return `${delta.toFixed(2)} vs ${label}`;
}

interface SummaryCardsProps {
  summary: NwiSummaryResponse;
  /** When set, show neutral metric deltas vs this baseline (e.g. "B vs A"). */
  diffFrom?: NwiSummaryResponse | null;
  /** Label for diff text, e.g. "A" so hint reads "vs A". */
  diffLabel?: string;
}

export function SummaryCards({ summary, diffFrom = null, diffLabel = "first" }: SummaryCardsProps) {
  const { metrics, upgrade_potential } = summary;
  const everyday = metrics?.everyday_convenience ?? null;
  const transit = metrics?.transit_viability ?? null;
  const variation = metrics?.variation ?? null;

  const baseEveryday = diffFrom?.metrics?.everyday_convenience ?? null;
  const baseTransit = diffFrom?.metrics?.transit_viability ?? null;
  const baseVariation = diffFrom?.metrics?.variation ?? null;
  const everydayDelta = formatDelta(everyday, baseEveryday, diffLabel);
  const transitDelta = formatDelta(transit, baseTransit, diffLabel);
  const variationDelta = formatDelta(variation, baseVariation, diffLabel);

  let upgradeVal: string;
  let upgradeCaption: string | null = null;
  if (upgrade_potential?.found && upgrade_potential.candidates?.length) {
    const best = upgrade_potential.candidates[0];
    const delta = best?.delta_nwi;
    const dist = best?.dist_miles;
    if (delta != null && dist != null) {
      upgradeVal = delta > 0 ? `+${delta.toFixed(1)}` : `${delta.toFixed(1)}`;
      upgradeCaption =
        upgrade_potential.candidates.length > 1
          ? `Best nearby (${dist.toFixed(1)} mi)`
          : `${dist.toFixed(1)} mi away`;
    } else {
      upgradeVal = "Found";
    }
  } else {
    upgradeVal = upgrade_potential?.message ?? "None found";
  }

  return (
    <section className="summary-cards" aria-label="Profile summary">
      <div className="summary-card" title="Average NWI score within the selected radius (higher = more walkable).">
        <div className="summary-card__value">{formatMetric(everyday)}</div>
        <div className="summary-card__label">Everyday Convenience</div>
        <div className="summary-card__hint">
          {everydayDelta ?? "Mean NWI within radius"}
        </div>
      </div>
      <div className="summary-card" title="Average transit proximity rank (1–20). EPA proxy d4a_ranked.">
        <div className="summary-card__value">{formatMetric(transit)}</div>
        <div className="summary-card__label">Transit Viability</div>
        <div className="summary-card__hint">
          {transitDelta ?? "Transit proximity rank (avg, 1–20)"}
        </div>
      </div>
      <div className="summary-card" title="Standard deviation of NWI within radius. Dispersion only.">
        <div className="summary-card__value">{formatMetric(variation)}</div>
        <div className="summary-card__label">Variation</div>
        <div className="summary-card__hint">
          {variationDelta ?? "Dispersion (std dev)"}
        </div>
      </div>
      <div className="summary-card" title="Best nearby candidate meeting min NWI improvement delta.">
        <div
          className={
            upgradeVal.length > 12
              ? "summary-card__value summary-card__value--text"
              : "summary-card__value"
          }
        >
          {upgradeVal}
        </div>
        <div className="summary-card__label">Upgrade Potential</div>
        {upgradeCaption && <div className="summary-card__hint">{upgradeCaption}</div>}
      </div>
    </section>
  );
}
