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
      <ResponsiveContainer
        width="100%"
        height={CHART_HEIGHTS.distribution}
        aria-label="Histogram showing distribution of component scores across block groups"
      >
        <BarChart data={data} margin={DISTRIBUTION_MARGINS}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="score"
            height={DISTRIBUTION_AXIS.xAxisHeight}
            label={{
              value: "Component Score (1-20)",
              position: "bottom",
              offset: 10,
              style: { fontSize: DISTRIBUTION_AXIS.axisLabelFontSize },
            }}
            aria-label="Component Score"
            domain={NWI_DOMAIN}
            interval={1}
            tick={{ fontSize: 11 }}
          />
          <YAxis
            width={DISTRIBUTION_AXIS.yAxisWidth}
            label={{
              value: "Number of Block Groups",
              angle: -90,
              position: "left",
              offset: DISTRIBUTION_AXIS.yAxisLabelOffset,
              style: { fontSize: DISTRIBUTION_AXIS.axisLabelFontSize },
            }}
            aria-label="Number of Block Groups"
            tick={{ fontSize: 11 }}
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
