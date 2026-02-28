/**
 * Component distribution histogram: shows distribution of each component score (1-20).
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { BlockGroupFeature } from "../../types/api";
import { COMPONENT_INFO, formatComponentLabel } from "../../lib/componentLabels";
import { COMPONENT_COLORS, CHART_HEIGHTS, NWI_DOMAIN, CHART_LAYOUT_PRESETS } from "../../lib/chartConfig";
import { ChartErrorBoundary } from "./ChartErrorBoundary";

interface ComponentDistributionChartProps {
  blockGroups: BlockGroupFeature[];
}

const { margin: DISTRIBUTION_MARGINS, axis: DISTRIBUTION_AXIS } = CHART_LAYOUT_PRESETS.distribution;
const DISTRIBUTION_LAYOUT = {
  margin: {
    ...DISTRIBUTION_MARGINS,
    top: 10,
    right: 10,
    bottom: 8,
    left: 44,
  },
  xAxisHeight: 30,
  yAxisWidth: 52,
} as const;
const distributionLegendItems = [
  { key: "d2a", label: formatComponentLabel(COMPONENT_INFO.d2a_ranked), color: COMPONENT_COLORS.d2a },
  { key: "d2b", label: formatComponentLabel(COMPONENT_INFO.d2b_ranked), color: COMPONENT_COLORS.d2b },
  { key: "d3b", label: formatComponentLabel(COMPONENT_INFO.d3b_ranked), color: COMPONENT_COLORS.d3b },
  { key: "d4a", label: formatComponentLabel(COMPONENT_INFO.d4a_ranked), color: COMPONENT_COLORS.d4a },
] as const;

export function ComponentDistributionChart({ blockGroups }: ComponentDistributionChartProps) {
  // Create histogram bins (1-20)
  const bins = Array.from({ length: 20 }, (_, i) => ({ score: i + 1 }));
  
  // Count occurrences for each component
  const d2aCounts = new Map<number, number>();
  const d2bCounts = new Map<number, number>();
  const d3bCounts = new Map<number, number>();
  const d4aCounts = new Map<number, number>();

  blockGroups.forEach((bg) => {
    if (bg.d2a_ranked != null) d2aCounts.set(bg.d2a_ranked, (d2aCounts.get(bg.d2a_ranked) || 0) + 1);
    if (bg.d2b_ranked != null) d2bCounts.set(bg.d2b_ranked, (d2bCounts.get(bg.d2b_ranked) || 0) + 1);
    if (bg.d3b_ranked != null) d3bCounts.set(bg.d3b_ranked, (d3bCounts.get(bg.d3b_ranked) || 0) + 1);
    if (bg.d4a_ranked != null) d4aCounts.set(bg.d4a_ranked, (d4aCounts.get(bg.d4a_ranked) || 0) + 1);
  });

  const data = bins.map((bin) => ({
    score: bin.score,
    d2a: d2aCounts.get(bin.score) || 0,
    d2b: d2bCounts.get(bin.score) || 0,
    d3b: d3bCounts.get(bin.score) || 0,
    d4a: d4aCounts.get(bin.score) || 0,
  }));

  return (
    <ChartErrorBoundary chartName="Component Distribution Chart">
      <div className="distribution-chart-layout">
        <div className="distribution-chart-layout__plot">
          <ResponsiveContainer
            width="100%"
            height={CHART_HEIGHTS.distribution}
            aria-label="Histogram showing distribution of component scores across block groups"
          >
            <BarChart data={data} margin={DISTRIBUTION_LAYOUT.margin}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="score"
                height={DISTRIBUTION_LAYOUT.xAxisHeight}
                label={{
                  value: "Component Score (1-20)",
                  position: "insideBottom",
                  offset: -2,
                  style: { fontSize: DISTRIBUTION_AXIS.axisLabelFontSize, fill: "#6b7280", fontFamily: "inherit" },
                }}
                aria-label="Component Score"
                domain={NWI_DOMAIN}
                interval={1}
                tickMargin={4}
                tick={{ fontSize: 11, fill: "#6b7280", fontFamily: "inherit" }}
              />
              <YAxis
                width={DISTRIBUTION_LAYOUT.yAxisWidth}
                aria-label="Number of Block Groups"
                tick={{ fontSize: 11, fill: "#6b7280", fontFamily: "inherit" }}
              />
              <Tooltip
                formatter={(value: number | undefined, name: string) => [`${value ?? 0}`, name]}
                labelFormatter={(label: number | string) => `Score bucket: ${String(label)}`}
              />
              <Bar
                dataKey="d2a"
                fill={COMPONENT_COLORS.d2a}
                name={formatComponentLabel(COMPONENT_INFO.d2a_ranked)}
                aria-label={`${COMPONENT_INFO.d2a_ranked.shortLabel} distribution`}
              />
              <Bar
                dataKey="d2b"
                fill={COMPONENT_COLORS.d2b}
                name={formatComponentLabel(COMPONENT_INFO.d2b_ranked)}
                aria-label={`${COMPONENT_INFO.d2b_ranked.shortLabel} distribution`}
              />
              <Bar
                dataKey="d3b"
                fill={COMPONENT_COLORS.d3b}
                name={formatComponentLabel(COMPONENT_INFO.d3b_ranked)}
                aria-label={`${COMPONENT_INFO.d3b_ranked.shortLabel} distribution`}
              />
              <Bar
                dataKey="d4a"
                fill={COMPONENT_COLORS.d4a}
                name={formatComponentLabel(COMPONENT_INFO.d4a_ranked)}
                aria-label={`${COMPONENT_INFO.d4a_ranked.shortLabel} distribution`}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="dashboard-chart-legend" aria-label="Distribution chart component legend">
        {distributionLegendItems.map((item) => (
          <span key={item.key} className="dashboard-chart-legend__item">
            <span className="dashboard-chart-legend__swatch" style={{ backgroundColor: item.color }} aria-hidden="true" />
            {item.label}
          </span>
        ))}
      </div>
    </ChartErrorBoundary>
  );
}
