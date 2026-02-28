/**
 * Component comparison: side-by-side comparison of component means.
 */

import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from "recharts";
import type { NwiSummaryResponse } from "../../types/api";
import { createComponentData, CHART_HEIGHTS, NWI_DOMAIN, CHART_LAYOUT_PRESETS } from "../../lib/chartConfig";
import { ChartErrorBoundary } from "./ChartErrorBoundary";

interface ComponentComparisonChartProps {
  summary: NwiSummaryResponse;
}

const { margin: COMPARISON_MARGINS, axis: COMPARISON_AXIS } = CHART_LAYOUT_PRESETS.comparison;

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
      <ResponsiveContainer
        width="100%"
        height={CHART_HEIGHTS.comparison}
        aria-label="Bar chart comparing component means sorted by strength"
      >
        <BarChart data={data} margin={COMPARISON_MARGINS}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            height={COMPARISON_AXIS.xAxisHeight}
            label={{
              value: "Component",
              position: "bottom",
              offset: 10,
              style: { fontSize: COMPARISON_AXIS.axisLabelFontSize },
            }}
            aria-label="Component"
          />
          <YAxis
            width={COMPARISON_AXIS.yAxisWidth}
            label={{
              value: "Average Score (1-20)",
              angle: -90,
              position: "left",
              offset: COMPARISON_AXIS.yAxisLabelOffset,
              style: { fontSize: COMPARISON_AXIS.axisLabelFontSize },
            }}
            domain={NWI_DOMAIN}
            aria-label="Average Score"
          />
          <Tooltip
            formatter={(value: number | undefined) => (value ?? 0).toFixed(2)}
            labelFormatter={(label: React.ReactNode) => {
              const labelStr = typeof label === "string" ? label : String(label ?? "");
              const item = data.find((d) => d.name === labelStr);
              return item ? `${item.name}: ${item.label}` : labelStr;
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
