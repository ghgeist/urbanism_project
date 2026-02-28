/**
 * Component correlation scatter plot: single-focus relationship view.
 */

import { useMemo, useState } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { BlockGroupFeature } from "../../types/api";
import { COMPONENT_INFO, formatComponentLabel } from "../../lib/componentLabels";
import { CHART_HEIGHTS, CHART_LAYOUT_PRESETS, NWI_DOMAIN, getComponentColor } from "../../lib/chartConfig";
import { calculateCorrelation } from "../../lib/correlation";
import { ChartErrorBoundary } from "./ChartErrorBoundary";

interface ComponentCorrelationChartProps {
  blockGroups: BlockGroupFeature[];
}

type ComponentKey = "d2a" | "d2b" | "d3b" | "d4a";

const COMPONENT_KEYS: ComponentKey[] = ["d2a", "d2b", "d3b", "d4a"];
const { margin: CORRELATION_CHART_MARGINS, axis: CORRELATION_AXIS } = CHART_LAYOUT_PRESETS.correlation;

type ScatterPoint = {
  nwi: number;
  component: number;
};

function buildTrendLine(points: ScatterPoint[]): [{ x: number; y: number }, { x: number; y: number }] | null {
  if (points.length < 2) {
    return null;
  }

  const n = points.length;
  const sumX = points.reduce((acc, p) => acc + p.nwi, 0);
  const sumY = points.reduce((acc, p) => acc + p.component, 0);
  const sumXY = points.reduce((acc, p) => acc + p.nwi * p.component, 0);
  const sumXX = points.reduce((acc, p) => acc + p.nwi * p.nwi, 0);
  const denominator = n * sumXX - sumX * sumX;

  if (denominator === 0) {
    return null;
  }

  const slope = (n * sumXY - sumX * sumY) / denominator;
  const intercept = (sumY - slope * sumX) / n;
  const xValues = points.map((p) => p.nwi);
  const minX = Math.min(...xValues);
  const maxX = Math.max(...xValues);
  return [
    { x: minX, y: intercept + slope * minX },
    { x: maxX, y: intercept + slope * maxX },
  ];
}

export function ComponentCorrelationChart({ blockGroups }: ComponentCorrelationChartProps) {
  const [activeComponent, setActiveComponent] = useState<ComponentKey>("d2a");
  const [showTrendLine, setShowTrendLine] = useState<boolean>(true);

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

  const scatterSeriesByComponent = useMemo(() => {
    return COMPONENT_KEYS.reduce<Record<ComponentKey, ScatterPoint[]>>((acc, key) => {
      acc[key] = data
        .filter((d) => d[key] != null)
        .map((d) => ({
          nwi: d.nwi,
          component: d[key]!,
        }));
      return acc;
    }, { d2a: [], d2b: [], d3b: [], d4a: [] });
  }, [data]);

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

  const selectedInfo = COMPONENT_INFO[`${activeComponent}_ranked` as keyof typeof COMPONENT_INFO];
  const selectedData = scatterSeriesByComponent[activeComponent];
  const selectedCorrelation = correlations[activeComponent];
  const selectedTrendLine = useMemo(() => buildTrendLine(selectedData), [selectedData]);

  if (data.length === 0) {
    return <p>No data available for correlation analysis.</p>;
  }

  return (
    <ChartErrorBoundary chartName="Component Correlation Chart">
      <div className="correlation-charts">
        <div className="correlation-intro">
          <p>Focus on one component at a time to inspect how it moves with NWI.</p>
          <div className="correlation-legend-toggles" role="radiogroup" aria-label="Select component for correlation chart">
            {COMPONENT_KEYS.map((key) => {
              const info = COMPONENT_INFO[`${key}_ranked` as keyof typeof COMPONENT_INFO];
              const isActive = key === activeComponent;
              return (
                <button
                  key={key}
                  type="button"
                  role="radio"
                  aria-checked={isActive}
                  className={`correlation-chip ${isActive ? "correlation-chip--active" : ""}`}
                  onClick={() => setActiveComponent(key)}
                  title={`r = ${correlations[key].toFixed(3)}`}
                >
                  <span
                    className="correlation-chip__dot"
                    style={{ backgroundColor: getComponentColor(key) }}
                    aria-hidden="true"
                  />
                  <span className="correlation-chip__label">{formatComponentLabel(info)}</span>
                </button>
              );
            })}
          </div>
          <div className="correlation-meta">
            <span>
              <strong>Correlation:</strong> r = {selectedCorrelation.toFixed(3)}
            </span>
            <button
              type="button"
              className={`correlation-trend-toggle ${showTrendLine ? "correlation-trend-toggle--active" : ""}`}
              aria-pressed={showTrendLine}
              onClick={() => setShowTrendLine((prev) => !prev)}
            >
              {showTrendLine ? "Trend line: On" : "Trend line: Off"}
            </button>
          </div>
        </div>
        <div className="correlation-chart-container" aria-label={`Scatter plot showing ${selectedInfo.shortLabel} versus NWI`}>
          <ResponsiveContainer width="100%" height={CHART_HEIGHTS.correlation}>
            <ScatterChart margin={CORRELATION_CHART_MARGINS}>
              <CartesianGrid stroke="#d1d5db" strokeDasharray="2 4" />
              <XAxis
                type="number"
                dataKey="nwi"
                name="NWI Score"
                height={CORRELATION_AXIS.xAxisHeight}
                label={{
                  value: "NWI Score",
                  position: "bottom",
                  offset: 10,
                  style: { fontSize: CORRELATION_AXIS.axisLabelFontSize },
                }}
                domain={NWI_DOMAIN}
                aria-label="NWI Score axis"
              />
              <YAxis
                type="number"
                dataKey="component"
                name={`${selectedInfo.code} Score`}
                width={CORRELATION_AXIS.yAxisWidth}
                label={{
                  value: `${selectedInfo.code} Score`,
                  angle: -90,
                  position: "left",
                  offset: CORRELATION_AXIS.yAxisLabelOffset,
                  style: { fontSize: CORRELATION_AXIS.axisLabelFontSize },
                }}
                domain={NWI_DOMAIN}
                aria-label={`${selectedInfo.shortLabel} score axis`}
              />
              <Tooltip
                cursor={{ strokeDasharray: "3 3" }}
                formatter={(value: number | undefined) => (value ?? 0).toFixed(2)}
                labelFormatter={(label: React.ReactNode) => `NWI: ${typeof label === "string" ? label : String(label ?? "")}`}
              />
              <Scatter
                name={formatComponentLabel(selectedInfo)}
                data={selectedData}
                fill={getComponentColor(activeComponent)}
                fillOpacity={0.65}
                legendType="none"
              />
              {showTrendLine && selectedTrendLine && (
                <ReferenceLine
                  segment={selectedTrendLine}
                  stroke={getComponentColor(activeComponent)}
                  strokeWidth={2}
                  strokeDasharray="6 4"
                />
              )}
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>
    </ChartErrorBoundary>
  );
}
