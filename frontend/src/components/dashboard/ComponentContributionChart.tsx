/**
 * Component contribution bar chart: shows average component scores vs NWI mean.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell } from "recharts";
import type { NwiSummaryResponse } from "../../types/api";
import { createComponentData, CHART_MARGINS, CHART_HEIGHTS, NWI_DOMAIN } from "../../lib/chartConfig";
import { ChartErrorBoundary } from "./ChartErrorBoundary";

interface ComponentContributionChartProps {
  summary: NwiSummaryResponse;
}

export function ComponentContributionChart({ summary }: ComponentContributionChartProps) {
  const { nwi } = summary;

  const data = createComponentData(summary).filter((d) => d.value != null);

  if (data.length === 0) {
    return <p>No component data available.</p>;
  }

  const nwiMean = nwi.mean ?? 0;

  return (
    <ChartErrorBoundary chartName="Component Contribution Chart">
      <ResponsiveContainer width="100%" height={CHART_HEIGHTS.compact} aria-label="Bar chart comparing component means to NWI average">
        <BarChart data={data} margin={CHART_MARGINS}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="component"
            label={{ value: "Component", position: "insideBottom", offset: -5 }}
            aria-label="Component"
          />
          <YAxis
            label={{ value: "Average Score (1-20)", angle: -90, position: "insideLeft" }}
            domain={NWI_DOMAIN}
            aria-label="Average Score"
          />
          <Tooltip formatter={(value: number) => value.toFixed(2)} />
          <Legend />
          <ReferenceLine
            y={nwiMean}
            stroke="#ff0000"
            strokeDasharray="3 3"
            label={{ value: `NWI Mean: ${nwiMean.toFixed(2)}`, position: "top" }}
            aria-label={`Reference line at NWI mean: ${nwiMean.toFixed(2)}`}
          />
          <Bar dataKey="value" name="Component Mean" aria-label="Component mean score">
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartErrorBoundary>
  );
}
