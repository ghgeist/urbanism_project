/**
 * Component comparison: side-by-side comparison of component means.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { NwiSummaryResponse } from "../../types/api";
import { COMPONENT_INFO } from "../../lib/componentLabels";

interface ComponentComparisonChartProps {
  summary: NwiSummaryResponse;
}

export function ComponentComparisonChart({ summary }: ComponentComparisonChartProps) {
  const { components } = summary;

  const data = [
    {
      name: COMPONENT_INFO.d2a_ranked.code,
      label: COMPONENT_INFO.d2a_ranked.shortLabel,
      value: components.employment_housing_mix_rank_mean,
    },
    {
      name: COMPONENT_INFO.d2b_ranked.code,
      label: COMPONENT_INFO.d2b_ranked.shortLabel,
      value: components.employment_type_diversity_rank_mean,
    },
    {
      name: COMPONENT_INFO.d3b_ranked.code,
      label: COMPONENT_INFO.d3b_ranked.shortLabel,
      value: components.intersection_density_rank_mean,
    },
    {
      name: COMPONENT_INFO.d4a_ranked.code,
      label: COMPONENT_INFO.d4a_ranked.shortLabel,
      value: components.transit_proximity_rank_mean_proxy,
    },
  ].filter((d) => d.value != null);

  if (data.length === 0) {
    return <p>No component data available.</p>;
  }

  // Sort by value descending to show strongest components first
  const sortedData = [...data].sort((a, b) => (b.value ?? 0) - (a.value ?? 0));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={sortedData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" label={{ value: "Component", position: "insideBottom", offset: -5 }} />
        <YAxis label={{ value: "Average Score (1-20)", angle: -90, position: "insideLeft" }} domain={[0, 20]} />
        <Tooltip 
          formatter={(value: number) => value.toFixed(2)} 
          labelFormatter={(label: string) => {
            const item = sortedData.find((d) => d.name === label);
            return item ? `${item.name}: ${item.label}` : label;
          }}
        />
        <Legend />
        <Bar dataKey="value" fill="#8884d8" name="Component Mean Score" />
      </BarChart>
    </ResponsiveContainer>
  );
}
