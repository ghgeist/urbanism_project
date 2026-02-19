/**
 * Component correlation scatter plot: shows relationship between components and NWI.
 * Includes component selector to view one component at a time for clarity.
 */

import { useState } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { BlockGroupFeature } from "../../types/api";
import { COMPONENT_INFO } from "../../lib/componentLabels";
import { ChartErrorBoundary } from "./ChartErrorBoundary";

interface ComponentCorrelationChartProps {
  blockGroups: BlockGroupFeature[];
}

type ComponentKey = "d2a" | "d2b" | "d3b" | "d4a";

const COMPONENT_KEYS: ComponentKey[] = ["d2a", "d2b", "d3b", "d4a"];

export function ComponentCorrelationChart({ blockGroups }: ComponentCorrelationChartProps) {
  const [selectedComponent, setSelectedComponent] = useState<ComponentKey>("d2a");

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

  const selectedData = data
    .filter((d) => d[selectedComponent] != null)
    .map((d) => ({
      nwi: d.nwi,
      component: d[selectedComponent]!,
    }));

  const selectedInfo = COMPONENT_INFO[`${selectedComponent}_ranked` as keyof typeof COMPONENT_INFO];
  const selectedCorrelation = correlations[selectedComponent];

  return (
    <ChartErrorBoundary chartName="Component Correlation Chart">
      <div className="correlation-charts">
        <div className="correlation-summary">
          <h3>Correlation with NWI Score</h3>
          <p style={{ margin: "0 0 0.75rem 0", fontSize: "0.9rem", color: "#6b7280" }}>
            Values range from -1 (negative correlation) to +1 (positive correlation). Higher positive values indicate stronger relationship with overall walkability.
          </p>
          <div className="correlation-component-selector" role="group" aria-label="Select component to view correlation">
            {COMPONENT_KEYS.map((key) => {
              const info = COMPONENT_INFO[`${key}_ranked` as keyof typeof COMPONENT_INFO];
              const isSelected = selectedComponent === key;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setSelectedComponent(key)}
                  className={`correlation-selector-btn ${isSelected ? "correlation-selector-btn--active" : ""}`}
                  aria-pressed={isSelected}
                  aria-label={`View correlation for ${info.shortLabel}`}
                >
                  <span className="correlation-selector-code">{info.code}</span>
                  <span className="correlation-selector-label">{info.shortLabel}</span>
                  <span className="correlation-selector-value">{correlations[key].toFixed(3)}</span>
                </button>
              );
            })}
          </div>
        </div>
        <div className="correlation-chart-container" aria-label={`Scatter plot showing ${selectedInfo.shortLabel} vs NWI Score`}>
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                type="number"
                dataKey="nwi"
                name="NWI Score"
                label={{ value: "NWI Score", position: "insideBottom", offset: -5 }}
                domain={[0, 20]}
                aria-label="NWI Score axis"
              />
              <YAxis
                type="number"
                dataKey="component"
                name="Component Score"
                label={{ value: `${selectedInfo.code} Score`, angle: -90, position: "insideLeft" }}
                domain={[0, 20]}
                aria-label={`${selectedInfo.shortLabel} Score axis`}
              />
              <Tooltip
                cursor={{ strokeDasharray: "3 3" }}
                formatter={(value: number) => value.toFixed(2)}
                labelFormatter={(label: string) => `NWI: ${label}`}
              />
              <Legend />
              <Scatter
                name={`${selectedInfo.code}: ${selectedInfo.shortLabel}`}
                data={selectedData}
                fill={
                  selectedComponent === "d2a"
                    ? "#8884d8"
                    : selectedComponent === "d2b"
                      ? "#82ca9d"
                      : selectedComponent === "d3b"
                        ? "#ffc658"
                        : "#ff7300"
                }
              />
            </ScatterChart>
          </ResponsiveContainer>
          <p className="correlation-chart-note" style={{ marginTop: "0.5rem", fontSize: "0.85rem", color: "#6b7280", textAlign: "center" }}>
            Correlation coefficient: <strong>{selectedCorrelation.toFixed(3)}</strong>
          </p>
        </div>
      </div>
    </ChartErrorBoundary>
  );
}
