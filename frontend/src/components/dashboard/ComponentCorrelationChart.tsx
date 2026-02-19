/**
 * Component correlation scatter plot: shows relationship between components and NWI.
 */

import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { BlockGroupFeature } from "../../types/api";
import { COMPONENT_INFO } from "../../lib/componentLabels";

interface ComponentCorrelationChartProps {
  blockGroups: BlockGroupFeature[];
}

export function ComponentCorrelationChart({ blockGroups }: ComponentCorrelationChartProps) {
  // Prepare data: component scores vs NWI
  const data = blockGroups
    .filter((bg) => bg.natwalkind != null)
    .map((bg) => ({
      nwi: bg.natwalkind!,
      d2a: bg.d2a_ranked,
      d2b: bg.d2b_ranked,
      d3b: bg.d3b_ranked,
      d4a: bg.d4a_ranked,
    }))
    .filter((d) => d.d2a != null || d.d2b != null || d.d3b != null || d.d4a != null);

  if (data.length === 0) {
    return <p>No data available for correlation analysis.</p>;
  }

  // Calculate correlation coefficient (simple Pearson correlation)
  function calculateCorrelation(x: (number | null)[], y: (number | null)[]): number {
    const pairs = x
      .map((xi, i) => ({ x: xi, y: y[i] }))
      .filter((p) => p.x != null && p.y != null) as { x: number; y: number }[];
    
    if (pairs.length < 2) return 0;

    const n = pairs.length;
    const sumX = pairs.reduce((sum, p) => sum + p.x, 0);
    const sumY = pairs.reduce((sum, p) => sum + p.y, 0);
    const sumXY = pairs.reduce((sum, p) => sum + p.x * p.y, 0);
    const sumX2 = pairs.reduce((sum, p) => sum + p.x * p.x, 0);
    const sumY2 = pairs.reduce((sum, p) => sum + p.y * p.y, 0);

    const numerator = n * sumXY - sumX * sumY;
    const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
    
    return denominator === 0 ? 0 : numerator / denominator;
  }

  const correlations = {
    d2a: calculateCorrelation(
      data.map((d) => d.d2a),
      data.map((d) => d.nwi)
    ),
    d2b: calculateCorrelation(
      data.map((d) => d.d2b),
      data.map((d) => d.nwi)
    ),
    d3b: calculateCorrelation(
      data.map((d) => d.d3b),
      data.map((d) => d.nwi)
    ),
    d4a: calculateCorrelation(
      data.map((d) => d.d4a),
      data.map((d) => d.nwi)
    ),
  };

  return (
    <div className="correlation-charts">
      <div className="correlation-summary">
        <h3>Correlation with NWI Score</h3>
        <p style={{ margin: "0 0 0.75rem 0", fontSize: "0.9rem", color: "#6b7280" }}>
          Values range from -1 (negative correlation) to +1 (positive correlation). Higher positive values indicate stronger relationship with overall walkability.
        </p>
        <ul>
          <li>{COMPONENT_INFO.d2a_ranked.code} ({COMPONENT_INFO.d2a_ranked.shortLabel}): <strong>{correlations.d2a.toFixed(3)}</strong></li>
          <li>{COMPONENT_INFO.d2b_ranked.code} ({COMPONENT_INFO.d2b_ranked.shortLabel}): <strong>{correlations.d2b.toFixed(3)}</strong></li>
          <li>{COMPONENT_INFO.d3b_ranked.code} ({COMPONENT_INFO.d3b_ranked.shortLabel}): <strong>{correlations.d3b.toFixed(3)}</strong></li>
          <li>{COMPONENT_INFO.d4a_ranked.code} ({COMPONENT_INFO.d4a_ranked.shortLabel}): <strong>{correlations.d4a.toFixed(3)}</strong></li>
        </ul>
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" dataKey="nwi" name="NWI Score" label={{ value: "NWI Score", position: "insideBottom", offset: -5 }} domain={[0, 20]} />
          <YAxis type="number" dataKey="component" name="Component Score" label={{ value: "Component Score", angle: -90, position: "insideLeft" }} domain={[0, 20]} />
          <Tooltip cursor={{ strokeDasharray: "3 3" }} formatter={(value: number) => value.toFixed(2)} />
          <Legend />
          <Scatter name={`${COMPONENT_INFO.d2a_ranked.code}: ${COMPONENT_INFO.d2a_ranked.shortLabel}`} data={data.filter((d) => d.d2a != null).map((d) => ({ nwi: d.nwi, component: d.d2a! }))} fill="#8884d8" />
          <Scatter name={`${COMPONENT_INFO.d2b_ranked.code}: ${COMPONENT_INFO.d2b_ranked.shortLabel}`} data={data.filter((d) => d.d2b != null).map((d) => ({ nwi: d.nwi, component: d.d2b! }))} fill="#82ca9d" />
          <Scatter name={`${COMPONENT_INFO.d3b_ranked.code}: ${COMPONENT_INFO.d3b_ranked.shortLabel}`} data={data.filter((d) => d.d3b != null).map((d) => ({ nwi: d.nwi, component: d.d3b! }))} fill="#ffc658" />
          <Scatter name={`${COMPONENT_INFO.d4a_ranked.code}: ${COMPONENT_INFO.d4a_ranked.shortLabel}`} data={data.filter((d) => d.d4a != null).map((d) => ({ nwi: d.nwi, component: d.d4a! }))} fill="#ff7300" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
