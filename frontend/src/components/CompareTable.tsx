import React from "react";
import type { NwiSummaryResponse } from "../types/api";

interface CompareTableProps {
  summaryA: NwiSummaryResponse | null;
  summaryB: NwiSummaryResponse | null;
}

function formatValue(val: number | null | undefined): string {
  if (val == null) return "—";
  return val.toFixed(2);
}

function formatDiff(valA: number | null | undefined, valB: number | null | undefined): React.ReactNode {
  if (valA == null || valB == null) return "—";
  const diff = valB - valA;
  if (Math.abs(diff) < 0.01) return <span className="diff-neutral">—</span>;

  const arrow = diff > 0 ? "↑" : "↓";
  const cls = diff > 0 ? "diff-positive" : "diff-negative";
  
  return (
    <span className={`diff ${cls}`}>
      {arrow} {Math.abs(diff).toFixed(2)}
    </span>
  );
}

import { METRICS_CONFIG } from "../config/metrics";

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
            return `+${best.delta_nwi.toFixed(1)} available`;
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
    isNumeric: true,
  }));

  const upgradeA = getUpgradeText(summaryA);
  const upgradeB = getUpgradeText(summaryB);
  const upgradeDiff = upgradeA === upgradeB ? "Same" : "—";

  return (
    <div className="compare-table-container">
      <table className="compare-table">
        <thead>
          <tr>
            <th className="col-metric">Metric</th>
            <th className="col-val-a">{summaryA.origin.label || "Location A"}</th>
            <th className="col-val-b">{summaryB.origin.label || "Location B"}</th>
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
              <td className="cell-val-a">{formatValue(row.valA)}</td>
              <td className="cell-val-b">{formatValue(row.valB)}</td>
              <td className="cell-diff">{formatDiff(row.valA, row.valB)}</td>
            </tr>
          ))}
          {/* Upgrade Potential is special because it's not a direct numeric comparison in the same way */}
          <tr className="row-upgrade">
            <td className="cell-metric">
                <div className="metric-label">Upgrade Potential</div>
                <div className="metric-desc">Best nearby improvement</div>
            </td>
            <td className="cell-val-a">{upgradeA}</td>
            <td className="cell-val-b">{upgradeB}</td>
            <td className="cell-diff">
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
