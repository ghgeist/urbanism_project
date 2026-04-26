import React from "react";
import type { NwiSummaryResponse } from "../types/api";
import { formatMetricValue, METRICS_CONFIG } from "../config/metrics";

interface CompareTableProps {
  summaryA: NwiSummaryResponse | null;
  summaryB: NwiSummaryResponse | null;
}

/** Neutral framing: no moral color coding (no red/green) per product plan. */
function formatDiff(valA: number | null | undefined, valB: number | null | undefined): React.ReactNode {
  if (valA == null || valB == null) return "—";
  const diff = valB - valA;
  if (Math.abs(diff) < 0.01) return <span className="diff-neutral">—</span>;

  const arrow = diff > 0 ? "↑" : "↓";
  return (
    <span className="diff diff-change">
      {arrow} {Math.abs(diff).toFixed(2)}
    </span>
  );
}

export function CompareTable({ summaryA, summaryB }: CompareTableProps) {
  if (!summaryA || !summaryB) {
    return null;
  }

  // Helper to extract upgrade potential text
  const getUpgradeText = (s: NwiSummaryResponse) => {
    const { upgrade_potential } = s;
    if (upgrade_potential?.found && upgrade_potential.candidates?.length) {
        const best = upgrade_potential.candidates[0];
        if (best.delta_nwi != null) {
            const nwiDelta = `${best.delta_nwi > 0 ? '+' : ''}${best.delta_nwi.toFixed(1)} NWI`;
            if (upgrade_potential.mode === "nwi_and_was" && best.delta_was != null) {
              return `${nwiDelta}, +${best.delta_was.toFixed(1)} WAS`;
            }
            return `${nwiDelta} (NWI-only)`;
        }
        return "Found";
    }
    return "None";
  };

  const rows = METRICS_CONFIG.map((config) => ({
    label: config.label,
    desc: config.description,
    tooltip: config.tooltip,
    valA: summaryA.metrics[config.key],
    valB: summaryB.metrics[config.key],
  }));

  const upgradeA = getUpgradeText(summaryA);
  const upgradeB = getUpgradeText(summaryB);
  const upgradeDiff = upgradeA === upgradeB ? "Same" : "—";

  const labelA = summaryA.origin.label || "Location A";
  const labelB = summaryB.origin.label || "Location B";

  return (
    <div className="compare-table-container">
      <table className="compare-table">
        <thead>
          <tr>
            <th className="col-metric">Metric</th>
            <th className="col-val-a">{labelA}</th>
            <th className="col-val-b">{labelB}</th>
            <th className="col-diff">Difference</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <td className="cell-metric">
                <div className="metric-label">
                  {row.label}
                  {row.tooltip && (
                    <span className="metric-help" aria-label={row.tooltip}>
                      ?
                      <span className="tooltip-content">{row.tooltip}</span>
                    </span>
                  )}
                </div>
                <div className="metric-desc">{row.desc}</div>
              </td>
              <td className="cell-val-a" data-label={labelA}>{formatMetricValue(row.valA)}</td>
              <td className="cell-val-b" data-label={labelB}>{formatMetricValue(row.valB)}</td>
              <td className="cell-diff" data-label="Difference">{formatDiff(row.valA, row.valB)}</td>
            </tr>
          ))}
          {/* Upgrade Potential is special because it's not a direct numeric comparison in the same way */}
          <tr className="row-upgrade">
            <td className="cell-metric">
                <div className="metric-label">Upgrade Potential</div>
                <div className="metric-desc">Best nearby NWI + amenity improvement when WAS is available</div>
            </td>
            <td className="cell-val-a" data-label={labelA}>{upgradeA}</td>
            <td className="cell-val-b" data-label={labelB}>{upgradeB}</td>
            <td className="cell-diff" data-label="Difference">
              <span className={upgradeDiff === "Same" ? "diff-neutral" : ""}>
                {upgradeDiff}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
