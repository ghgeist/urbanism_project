/**
 * Component comparison: side-by-side comparison of component means.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from "recharts";
import type { NwiSummaryResponse } from "../../types/api";
import { createComponentData, CHART_MARGINS, CHART_HEIGHTS, NWI_DOMAIN } from "../../lib/chartConfig";
import { ChartErrorBoundary } from "./ChartErrorBoundary";

interface ComponentComparisonChartProps {
  summary: NwiSummaryResponse;
}

export function ComponentComparisonChart({ summary }: ComponentComparisonChartProps) {
  const componentData = createComponentData(summary).filter((d) => d.value != null);

  if (componentData.length === 0) {
    return <p>No component data available.</p>;
  }

  // Sort by value descending to show strongest components first
  const sortedData = [...componentData].sort((a, b) => (b.value ?? 0) - (a.value ?? 0));

  // Map to chart data format while preserving color
  const data = sortedData.map((d) => ({
    name: d.component,
    label: d.label,
    value: d.value,
    color: d.color,
  }));

  return (
    <ChartErrorBoundary chartName="Component Comparison Chart">
      <ResponsiveContainer width="100%" height={CHART_HEIGHTS.compact} aria-label="Bar chart comparing component means sorted by strength">
        <BarChart data={data} margin={CHART_MARGINS}>
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
              const item = data.find((d) => d.name === label);
              return item ? `${item.name}: ${item.label}` : label;
            }}
          />
          <Legend />
          <Bar dataKey="value" name="Component Mean Score" aria-label="Component mean score">
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartErrorBoundary>
  );
}
