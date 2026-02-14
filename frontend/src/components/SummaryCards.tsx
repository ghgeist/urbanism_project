/**
 * Four summary cards: Everyday Convenience, Transit Viability, Variation, Upgrade Potential.
 * Neutral descriptors only; no moral color coding per product plan.
 * Optional diffFrom: when set (e.g. Compare page B panel), show neutral delta vs baseline.
 */

import type { NwiSummaryResponse } from "../types/api";
import { METRICS_CONFIG } from "../config/metrics";

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
        const baseVal = diffFrom?.metrics?.[config.key] ?? null;
        const delta = formatDelta(val, baseVal, diffLabel);
        
        return (
          <div key={config.key} className="summary-card" title={config.tooltip}>
            <div className="summary-card__value">{formatMetric(val)}</div>
            <div className="summary-card__label">{config.label}</div>
            <div className="summary-card__hint">
              {delta ?? config.description}
            </div>
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

