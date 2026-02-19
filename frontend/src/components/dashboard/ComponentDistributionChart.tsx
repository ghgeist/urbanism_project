/**
 * Component distribution histogram: shows distribution of each component score (1-20).
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { BlockGroupFeature } from "../../types/api";
import { COMPONENT_INFO } from "../../lib/componentLabels";

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
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="score" label={{ value: "Component Score (1-20)", position: "insideBottom", offset: -5 }} />
        <YAxis label={{ value: "Number of Block Groups", angle: -90, position: "insideLeft" }} />
        <Tooltip />
        <Legend />
        <Bar dataKey="d2a" fill="#8884d8" name={`${COMPONENT_INFO.d2a_ranked.code}: ${COMPONENT_INFO.d2a_ranked.shortLabel}`} />
        <Bar dataKey="d2b" fill="#82ca9d" name={`${COMPONENT_INFO.d2b_ranked.code}: ${COMPONENT_INFO.d2b_ranked.shortLabel}`} />
        <Bar dataKey="d3b" fill="#ffc658" name={`${COMPONENT_INFO.d3b_ranked.code}: ${COMPONENT_INFO.d3b_ranked.shortLabel}`} />
        <Bar dataKey="d4a" fill="#ff7300" name={`${COMPONENT_INFO.d4a_ranked.code}: ${COMPONENT_INFO.d4a_ranked.shortLabel}`} />
      </BarChart>
    </ResponsiveContainer>
  );
}
