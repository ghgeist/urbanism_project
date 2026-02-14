/**
 * Four summary cards: Everyday Convenience, Transit Viability, Variation, Upgrade Potential.
 * Neutral descriptors only; no moral color coding per product plan.
 */

import type { NwiSummaryResponse } from "../types/api";
import { formatMetricValue, METRICS_CONFIG } from "../config/metrics";

interface SummaryCardsProps {
  summary: NwiSummaryResponse;
}

export function SummaryCards({ summary }: SummaryCardsProps) {
  const { metrics, upgrade_potential } = summary;

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
      {METRICS_CONFIG.map((config) => {
        const val = metrics?.[config.key] ?? null;
        return (
          <div key={config.key} className="summary-card" title={config.tooltip}>
            <div className="summary-card__value">{formatMetricValue(val)}</div>
            <div className="summary-card__label">{config.label}</div>
            <div className="summary-card__hint">{config.description}</div>
          </div>
        );
      })}
      
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

