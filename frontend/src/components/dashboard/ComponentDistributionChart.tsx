/**
 * Component distribution histogram: shows distribution of each component score (1-20).
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { BlockGroupFeature } from "../../types/api";
import { COMPONENT_INFO } from "../../lib/componentLabels";
import { COMPONENT_COLORS, CHART_MARGINS, CHART_HEIGHTS, NWI_DOMAIN } from "../../lib/chartConfig";
import { ChartErrorBoundary } from "./ChartErrorBoundary";

interface ComponentDistributionChartProps {
  blockGroups: BlockGroupFeature[];
}

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
      <ResponsiveContainer width="100%" height={CHART_HEIGHTS.standard} aria-label="Histogram showing distribution of component scores across block groups">
        <BarChart data={data} margin={CHART_MARGINS}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="score"
            label={{ value: "Component Score (1-20)", position: "insideBottom", offset: -5 }}
            aria-label="Component Score"
            domain={NWI_DOMAIN}
          />
          <YAxis
            label={{ value: "Number of Block Groups", angle: -90, position: "insideLeft" }}
            aria-label="Number of Block Groups"
          />
          <Tooltip />
          <Legend />
          <Bar
            dataKey="d2a"
            fill={COMPONENT_COLORS.d2a}
            name={`${COMPONENT_INFO.d2a_ranked.code}: ${COMPONENT_INFO.d2a_ranked.shortLabel}`}
            aria-label={`${COMPONENT_INFO.d2a_ranked.shortLabel} distribution`}
          />
          <Bar
            dataKey="d2b"
            fill={COMPONENT_COLORS.d2b}
            name={`${COMPONENT_INFO.d2b_ranked.code}: ${COMPONENT_INFO.d2b_ranked.shortLabel}`}
            aria-label={`${COMPONENT_INFO.d2b_ranked.shortLabel} distribution`}
          />
          <Bar
            dataKey="d3b"
            fill={COMPONENT_COLORS.d3b}
            name={`${COMPONENT_INFO.d3b_ranked.code}: ${COMPONENT_INFO.d3b_ranked.shortLabel}`}
            aria-label={`${COMPONENT_INFO.d3b_ranked.shortLabel} distribution`}
          />
          <Bar
            dataKey="d4a"
            fill={COMPONENT_COLORS.d4a}
            name={`${COMPONENT_INFO.d4a_ranked.code}: ${COMPONENT_INFO.d4a_ranked.shortLabel}`}
            aria-label={`${COMPONENT_INFO.d4a_ranked.shortLabel} distribution`}
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartErrorBoundary>
  );
}
