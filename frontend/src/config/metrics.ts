/**
 * Centralized configuration for NWI metrics.
 * Ensures consistent labels, descriptions, tooltips, and number formatting across SummaryCards and CompareTable.
 */

import type { Metrics } from "../types/api";

/** Format a metric value for display; null/undefined → "—", otherwise 2 decimal places. */
export function formatMetricValue(val: number | null | undefined): string {
  if (val == null) return "—";
  return val.toFixed(2);
}

export interface MetricConfig {
  key: keyof Metrics;
  label: string;
  description: string;
  tooltip: string;
}

export const METRICS_CONFIG: MetricConfig[] = [
  {
    key: "everyday_convenience",
    label: "Everyday Convenience",
    description: "Mean NWI within radius",
    tooltip: "NWI: 1–20, higher = more walkable",
  },
  {
    key: "transit_viability",
    label: "Transit Viability",
    description: "Transit proximity rank (1–20)",
    tooltip: "Transit rank: 1–20, higher = closer to transit",
  },
  {
    key: "variation",
    label: "Variation",
    description: "Dispersion (std dev)",
    tooltip: "Variation: higher = more mixed environment",
  },
];
