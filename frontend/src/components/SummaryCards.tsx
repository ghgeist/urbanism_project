/**
 * Five summary cards: Everyday Convenience, Transit Viability, Variation,
 * Amenity Richness (WAS), Upgrade Potential.
 * Neutral descriptors only; no moral color coding per product plan.
 */

import type { NwiSummaryResponse } from "../types/api";
import { formatMetricValue, METRICS_CONFIG } from "../config/metrics";

interface SummaryCardsProps {
  summary: NwiSummaryResponse;
}

export function SummaryCards({ summary }: SummaryCardsProps) {
  const { metrics, upgrade_potential, amenity_richness } = summary;

  let upgradeVal: string;
  let upgradeCaption: string | null = null;
  const upgradeMode = upgrade_potential?.mode ?? "nwi_only";
  if (upgrade_potential?.found && upgrade_potential.candidates?.length) {
    const best = upgrade_potential.candidates[0];
    const delta = best?.delta_nwi;
    const deltaWas = best?.delta_was;
    const dist = best?.dist_miles;
    if (delta != null && dist != null) {
      upgradeVal = delta > 0 ? `+${delta.toFixed(1)}` : `${delta.toFixed(1)}`;
      const modeLabel =
        upgradeMode === "nwi_and_was" && deltaWas != null
          ? `NWI + amenities (+${deltaWas.toFixed(1)} WAS)`
          : "NWI-only";
      upgradeCaption = `${modeLabel} · ${dist.toFixed(1)} mi away`;
    } else {
      upgradeVal = "Found";
      upgradeCaption = upgradeMode === "nwi_and_was" ? "NWI + amenities" : "NWI-only";
    }
  } else {
    upgradeVal = upgrade_potential?.message ?? "None found";
  }

  // Amenity Richness: mean WAS score + human-readable bucket. Render "—" when
  // the WAS table isn't loaded or no selected BGs are in WAS coverage.
  const amenityValue = amenity_richness?.value;
  const amenityLabel = amenity_richness?.label;
  const amenityCaption =
    amenityLabel && amenityLabel !== "Unavailable"
      ? amenityLabel
      : "WAS 2019 data unavailable for this area";

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

      <div
        className="summary-card"
        title="Mean Walkable Accessibility Score (WAS) 2019, 0-30. Higher = more reachable destinations (groceries, shops, schools, parks, food) within a comfortable walk. Source: Credit et al. (2025). See the Method page for the full citation."
      >
        <div className="summary-card__value">{formatMetricValue(amenityValue)}</div>
        <div className="summary-card__label">Amenity Richness</div>
        <div className="summary-card__hint">{amenityCaption}</div>
      </div>

      <div className="summary-card" title="Best nearby candidate meeting the minimum EPA walkability (NWI) improvement threshold and, when available, at least +2.0 Walkable Accessibility Score (WAS) points. Falls back to NWI-only when WAS data is unavailable.">
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

