/**
 * Component contribution bar chart: shows average component scores vs NWI mean.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from "recharts";
import type { NwiSummaryResponse } from "../../types/api";
import { COMPONENT_INFO } from "../../lib/componentLabels";
import { ChartErrorBoundary } from "./ChartErrorBoundary";

interface ComponentContributionChartProps {
  summary: NwiSummaryResponse;
}

export function ComponentContributionChart({ summary }: ComponentContributionChartProps) {
  const { components, nwi } = summary;

  const data = [
    {
      component: COMPONENT_INFO.d2a_ranked.code,
      label: COMPONENT_INFO.d2a_ranked.shortLabel,
      value: components.employment_housing_mix_rank_mean,
    },
    {
      component: COMPONENT_INFO.d2b_ranked.code,
      label: COMPONENT_INFO.d2b_ranked.shortLabel,
      value: components.employment_type_diversity_rank_mean,
    },
    {
      component: COMPONENT_INFO.d3b_ranked.code,
      label: COMPONENT_INFO.d3b_ranked.shortLabel,
      value: components.intersection_density_rank_mean,
    },
    {
      component: COMPONENT_INFO.d4a_ranked.code,
      label: COMPONENT_INFO.d4a_ranked.shortLabel,
      value: components.transit_proximity_rank_mean_proxy,
    },
  ].filter((d) => d.value != null);

  if (data.length === 0) {
    return <p>No component data available.</p>;
  }

  const nwiMean = nwi.mean ?? 0;

  return (
    <ChartErrorBoundary chartName="Component Contribution Chart">
      <ResponsiveContainer width="100%" height={300} aria-label="Bar chart comparing component means to NWI average">
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="component"
            label={{ value: "Component", position: "insideBottom", offset: -5 }}
            aria-label="Component"
          />
          <YAxis
            label={{ value: "Average Score (1-20)", angle: -90, position: "insideLeft" }}
            domain={[0, 20]}
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
          <Bar dataKey="value" fill="#8884d8" name="Component Mean" aria-label="Component mean score" />
        </BarChart>
      </ResponsiveContainer>
    </ChartErrorBoundary>
  );
}
