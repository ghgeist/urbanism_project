/**
 * Four summary cards: Everyday Convenience, Transit Viability, Variation, Upgrade Potential.
 * Neutral descriptors only; no moral color coding per product plan.
 */

import type { NwiSummaryResponse } from "../types/api";

function formatMetric(value: number | null | undefined): string {
  if (value == null) return "—";
  return value.toFixed(2);
}

interface SummaryCardsProps {
  summary: NwiSummaryResponse;
}

export function SummaryCards({ summary }: SummaryCardsProps) {
  const { metrics, upgrade_potential } = summary;
  const everyday = metrics?.everyday_convenience ?? null;
  const transit = metrics?.transit_viability ?? null;
  const variation = metrics?.variation ?? null;

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
        <div className="summary-card__hint">Mean NWI within radius</div>
      </div>
      <div className="summary-card" title="Average transit proximity rank (1–20). EPA proxy d4a_ranked.">
        <div className="summary-card__value">{formatMetric(transit)}</div>
        <div className="summary-card__label">Transit Viability</div>
        <div className="summary-card__hint">Transit proximity rank (avg, 1–20)</div>
      </div>
      <div className="summary-card" title="Standard deviation of NWI within radius. Dispersion only.">
        <div className="summary-card__value">{formatMetric(variation)}</div>
        <div className="summary-card__label">Variation</div>
        <div className="summary-card__hint">Dispersion (std dev)</div>
      </div>
      <div className="summary-card" title="Best nearby candidate meeting min NWI improvement delta.">
        <div className="summary-card__value">{upgradeVal}</div>
        <div className="summary-card__label">Upgrade Potential</div>
        {upgradeCaption && <div className="summary-card__hint">{upgradeCaption}</div>}
      </div>
    </section>
  );
}
