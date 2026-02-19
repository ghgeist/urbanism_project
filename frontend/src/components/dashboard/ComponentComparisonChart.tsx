/**
 * Component comparison: side-by-side comparison of component means.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { NwiSummaryResponse } from "../../types/api";
import { createComponentData, CHART_MARGINS, CHART_HEIGHTS, NWI_DOMAIN } from "../../lib/chartConfig";
import { ChartErrorBoundary } from "./ChartErrorBoundary";

interface ComponentComparisonChartProps {
  summary: NwiSummaryResponse;
}

export function ComponentComparisonChart({ summary }: ComponentComparisonChartProps) {
  const data = createComponentData(summary)
    .map((d) => ({
      name: d.component,
      label: d.label,
      value: d.value,
    }))
    .filter((d) => d.value != null);

  if (data.length === 0) {
    return <p>No component data available.</p>;
  }

  // Sort by value descending to show strongest components first
  const sortedData = [...data].sort((a, b) => (b.value ?? 0) - (a.value ?? 0));

  return (
    <ChartErrorBoundary chartName="Component Comparison Chart">
      <ResponsiveContainer width="100%" height={CHART_HEIGHTS.compact} aria-label="Bar chart comparing component means sorted by strength">
        <BarChart data={sortedData} margin={CHART_MARGINS}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            label={{ value: "Component", position: "insideBottom", offset: -5 }}
            aria-label="Component"
          />
          <YAxis
            label={{ value: "Average Score (1-20)", angle: -90, position: "insideLeft" }}
            domain={NWI_DOMAIN}
            aria-label="Average Score"
          />
          <Tooltip
            formatter={(value: number) => value.toFixed(2)}
            labelFormatter={(label: string) => {
              const item = sortedData.find((d) => d.name === label);
              return item ? `${item.name}: ${item.label}` : label;
            }}
          />
          <Legend />
          <Bar dataKey="value" fill="#8884d8" name="Component Mean Score" aria-label="Component mean score" />
        </BarChart>
      </ResponsiveContainer>
    </ChartErrorBoundary>
  );
}
