/**
 * Component contribution bar chart: shows average component scores vs NWI mean.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { NwiSummaryResponse } from "../../types/api";
import { createComponentData, CHART_HEIGHTS, NWI_DOMAIN, CHART_LAYOUT_PRESETS } from "../../lib/chartConfig";
import { ChartErrorBoundary } from "./ChartErrorBoundary";

interface ComponentContributionChartProps {
  summary: NwiSummaryResponse;
}

const { margin: CONTRIBUTION_MARGINS, axis: CONTRIBUTION_AXIS } = CHART_LAYOUT_PRESETS.contribution;
const CONTRIBUTION_LAYOUT = {
  margin: {
    ...CONTRIBUTION_MARGINS,
    top: 12,
    right: 16,
    bottom: 8,
    left: 18,
  },
  xAxisHeight: 32,
  yAxisWidth: 180,
} as const;

export function ComponentContributionChart({ summary }: ComponentContributionChartProps) {
  const data = createComponentData(summary).filter((d) => d.value != null);

  if (data.length === 0) {
    return <p>No component data available.</p>;
  }

  return (
    <ChartErrorBoundary chartName="Component Contribution Chart">
      <ResponsiveContainer
        width="100%"
        height={CHART_HEIGHTS.contribution}
        aria-label="Bar chart comparing component means to NWI average"
      >
        <BarChart data={data} margin={CONTRIBUTION_LAYOUT.margin} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            type="number"
            domain={NWI_DOMAIN}
            height={CONTRIBUTION_LAYOUT.xAxisHeight}
            tickMargin={4}
            tick={{ fontSize: 11, fill: "#6b7280", fontFamily: "inherit" }}
            label={{
              value: "Average Score",
              position: "insideBottom",
              offset: -2,
              style: { fontSize: CONTRIBUTION_AXIS.axisLabelFontSize, fill: "#6b7280", fontFamily: "inherit" },
            }}
            aria-label="Average Score"
          />
          <YAxis
            type="category"
            dataKey="component"
            width={CONTRIBUTION_LAYOUT.yAxisWidth}
            tick={{ fontSize: 11, fill: "#6b7280", fontFamily: "inherit" }}
            interval={0}
            aria-label="Component"
          />
          <Tooltip formatter={(value: number | undefined) => (value ?? 0).toFixed(2)} />
          <Bar dataKey="value" aria-label="Component mean score">
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartErrorBoundary>
  );
}
