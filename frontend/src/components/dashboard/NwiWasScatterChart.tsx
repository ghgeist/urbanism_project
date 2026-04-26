/**
 * Walkability vs amenities scatter plot.
 */

import { useMemo } from "react";
import {
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { NwiSummaryResponse } from "../../types/api";
import {
  buildNwiWasPoints,
  countNwiWasQuadrants,
  DEFAULT_HIGH_NWI_THRESHOLD,
  DEFAULT_LOW_WAS_THRESHOLD,
  NWI_WAS_QUADRANT_INFO,
  type NwiWasPoint,
  type NwiWasQuadrant,
} from "../../lib/nwiWasAnalytics";
import { CHART_HEIGHTS, CHART_LAYOUT_PRESETS, NWI_DOMAIN, WAS_DOMAIN } from "../../lib/chartConfig";
import { ChartErrorBoundary } from "./ChartErrorBoundary";

interface NwiWasScatterChartProps {
  summary: NwiSummaryResponse;
}

interface ScatterTooltipProps {
  active?: boolean;
  payload?: Array<{ payload?: NwiWasPoint }>;
}

const QUADRANT_ORDER: NwiWasQuadrant[] = [
  "walkableDestinations",
  "hollowNeighborhood",
  "destinationRichLowerNwi",
  "sparseLowerNwi",
];
const { margin: NWI_WAS_CHART_MARGINS, axis: NWI_WAS_AXIS } = CHART_LAYOUT_PRESETS.nwiWas;

function formatThreshold(value: number): string {
  return Number.isInteger(value) ? value.toFixed(0) : value.toFixed(1);
}

function NwiWasTooltip({ active, payload }: ScatterTooltipProps) {
  if (!active || !payload?.[0]?.payload) {
    return null;
  }

  const point = payload[0].payload;
  const info = NWI_WAS_QUADRANT_INFO[point.quadrant];

  return (
    <div className="nwi-was-tooltip">
      <strong>{point.geoid20 ?? "Block group"}</strong>
      <span>{info.label}</span>
      <span>National Walkability Index: {point.nwi.toFixed(2)}</span>
      <span>Amenity access score: {point.was.toFixed(2)}</span>
    </div>
  );
}

export function NwiWasScatterChart({ summary }: NwiWasScatterChartProps) {
  const highNwiThreshold = summary.hollow_neighborhood?.nwi_threshold ?? DEFAULT_HIGH_NWI_THRESHOLD;
  const lowWasThreshold = summary.hollow_neighborhood?.was_threshold ?? DEFAULT_LOW_WAS_THRESHOLD;
  const thresholds = useMemo(
    () => ({ highNwiThreshold, lowWasThreshold }),
    [highNwiThreshold, lowWasThreshold]
  );
  const points = useMemo(() => buildNwiWasPoints(summary.block_groups, thresholds), [summary.block_groups, thresholds]);
  const counts = useMemo(() => countNwiWasQuadrants(points), [points]);
  const series = useMemo(
    () =>
      QUADRANT_ORDER.map((quadrant) => ({
        quadrant,
        points: points.filter((point) => point.quadrant === quadrant),
      })),
    [points]
  );
  const hollowCount = counts.hollowNeighborhood;

  if (points.length === 0) {
    return (
      <div className="nwi-was-empty">
        <p>WAS data is unavailable for the selected block groups.</p>
        <p>Load the WAS table or choose an area with WAS coverage to compare NWI and destination access.</p>
      </div>
    );
  }

  return (
    <ChartErrorBoundary chartName="Walkability vs Amenities Chart">
      <div className="nwi-was-chart">
        <div className="correlation-header">
          <div className="correlation-header__title-group">
            <p className="correlation-header__eyebrow">Integration analytics</p>
            <h3>Walkability vs Amenities</h3>
            <p className="correlation-header__hint">
              Each point is a block group. National Walkability Index (NWI) measures built form; Walkable
              Accessibility Score (WAS) measures reachable destinations.
            </p>
          </div>
          <div className="correlation-header__metric" aria-live="polite">
            <span className="correlation-header__metric-label">Hollow candidates</span>
            <strong className="correlation-header__metric-value">{hollowCount}</strong>
            <span className="correlation-header__metric-description">
              High NWI (&gt;= {formatThreshold(thresholds.highNwiThreshold)}) with low WAS (&lt;={" "}
              {formatThreshold(thresholds.lowWasThreshold)})
            </span>
          </div>
        </div>

        <div className="correlation-chart-container">
          <ResponsiveContainer
            width="100%"
            height={CHART_HEIGHTS.nwiWas}
            aria-label="Scatter chart comparing National Walkability Index and Walkable Accessibility Score"
          >
            <ScatterChart margin={NWI_WAS_CHART_MARGINS}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                type="number"
                dataKey="nwi"
                name="NWI"
                domain={NWI_DOMAIN}
                height={NWI_WAS_AXIS.xAxisHeight}
                tickMargin={4}
                tick={{ fontSize: 11, fill: "#6b7280", fontFamily: "inherit" }}
                label={{
                  value: "National Walkability Index, NWI (1-20)",
                  position: "insideBottom",
                  offset: -4,
                  style: { fontSize: NWI_WAS_AXIS.axisLabelFontSize, fill: "#6b7280", fontFamily: "inherit" },
                }}
              />
              <YAxis
                type="number"
                dataKey="was"
                name="WAS"
                domain={WAS_DOMAIN}
                width={NWI_WAS_AXIS.yAxisWidth}
                tick={{ fontSize: 11, fill: "#6b7280", fontFamily: "inherit" }}
                label={{
                  value: "Walkable Accessibility Score, WAS (0-30)",
                  angle: -90,
                  position: "insideLeft",
                  offset: NWI_WAS_AXIS.yAxisLabelOffset,
                  style: { fontSize: NWI_WAS_AXIS.axisLabelFontSize, fill: "#6b7280", fontFamily: "inherit" },
                }}
              />
              <ReferenceLine x={thresholds.highNwiThreshold} stroke="#94a3b8" strokeDasharray="4 4" />
              <ReferenceLine y={thresholds.lowWasThreshold} stroke="#94a3b8" strokeDasharray="4 4" />
              <Tooltip content={<NwiWasTooltip />} />
              {series.map(({ quadrant, points: quadrantPoints }) => (
                <Scatter
                  key={quadrant}
                  name={NWI_WAS_QUADRANT_INFO[quadrant].label}
                  data={quadrantPoints}
                  fill={NWI_WAS_QUADRANT_INFO[quadrant].color}
                  isAnimationActive={false}
                />
              ))}
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        <div className="dashboard-chart-legend" aria-label="NWI versus WAS quadrant legend">
          {QUADRANT_ORDER.map((quadrant) => {
            const info = NWI_WAS_QUADRANT_INFO[quadrant];
            return (
              <span key={quadrant} className="dashboard-chart-legend__item">
                <span
                  className="dashboard-chart-legend__swatch"
                  style={{ backgroundColor: info.color }}
                  aria-hidden="true"
                />
                {info.shortLabel}: {counts[quadrant]}
              </span>
            );
          })}
        </div>
        <p className="nwi-was-color-note">
          Colors group block groups by whether they are above or below the NWI and WAS guide lines. The amber group is
          the Hollow Neighborhood pattern: walkable form with sparse nearby amenities.
        </p>
      </div>
    </ChartErrorBoundary>
  );
}
