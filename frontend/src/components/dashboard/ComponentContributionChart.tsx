/**
 * Component contribution bar chart: shows average component scores vs NWI mean.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from "recharts";
import type { NwiSummaryResponse } from "../../types/api";
import { createComponentData, CHART_HEIGHTS, NWI_DOMAIN, CHART_LAYOUT_PRESETS } from "../../lib/chartConfig";
import { ChartErrorBoundary } from "./ChartErrorBoundary";

interface ComponentContributionChartProps {
  summary: NwiSummaryResponse;
}

const { margin: CONTRIBUTION_MARGINS, axis: CONTRIBUTION_AXIS } = CHART_LAYOUT_PRESETS.contribution;

export function ComponentContributionChart({ summary }: ComponentContributionChartProps) {
  const { nwi } = summary;

  const data = createComponentData(summary).filter((d) => d.value != null);

  if (data.length === 0) {
    return <p>No component data available.</p>;
  }

  const nwiMean = nwi.mean ?? 0;

  return (
    <ChartErrorBoundary chartName="Component Contribution Chart">
      <ResponsiveContainer
        width="100%"
        height={CHART_HEIGHTS.contribution}
        aria-label="Bar chart comparing component means to NWI average"
      >
        <BarChart data={data} margin={CONTRIBUTION_MARGINS}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="component"
            height={CONTRIBUTION_AXIS.xAxisHeight}
            tick={{ fontSize: 11, fill: "#6b7280", fontFamily: "inherit" }}
            label={{
              value: "Component",
              position: "bottom",
              offset: 10,
              style: { fontSize: CONTRIBUTION_AXIS.axisLabelFontSize, fill: "#6b7280", fontFamily: "inherit" },
            }}
            aria-label="Component"
          />
          <YAxis
            width={CONTRIBUTION_AXIS.yAxisWidth}
            tick={{ fontSize: 11, fill: "#6b7280", fontFamily: "inherit" }}
            label={{
              value: "Average Score",
              angle: -90,
              position: "left",
              offset: 8,
              style: {
                fontSize: CONTRIBUTION_AXIS.axisLabelFontSize,
                fill: "#6b7280",
                fontFamily: "inherit",
                fontWeight: 500,
              },
            }}
            domain={NWI_DOMAIN}
            aria-label="Average Score"
          />
          <Tooltip formatter={(value: number | undefined) => (value ?? 0).toFixed(2)} />
          <ReferenceLine
            y={nwiMean}
            stroke="#ff0000"
            strokeDasharray="3 3"
            label={{ value: `NWI Mean: ${nwiMean.toFixed(2)}`, position: "top" }}
            aria-label={`Reference line at NWI mean: ${nwiMean.toFixed(2)}`}
          />
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
