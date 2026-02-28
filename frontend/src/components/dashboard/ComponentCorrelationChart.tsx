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
const TREND_LINE_COLORS: Record<ComponentKey, string> = {
  d2a: "#5b54b3",
  d2b: "#3d8b5a",
  d3b: "#a16207",
  d4a: "#c2410c",
};

type ScatterPoint = {
  nwi: number;
  component: number;
};

function getCorrelationDescriptor(correlation: number): string {
  const abs = Math.abs(correlation);
  if (abs >= 0.8) {
    return correlation >= 0 ? "Very strong positive relationship" : "Very strong negative relationship";
  }
  if (abs >= 0.6) {
    return correlation >= 0 ? "Strong positive relationship" : "Strong negative relationship";
  }
  if (abs >= 0.4) {
    return correlation >= 0 ? "Moderate positive relationship" : "Moderate negative relationship";
  }
  if (abs >= 0.2) {
    return correlation >= 0 ? "Weak positive relationship" : "Weak negative relationship";
  }
  return "Little to no linear relationship";
}

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

  if (!Number.isFinite(slope) || !Number.isFinite(intercept)) {
    return null;
  }

  const [minBound, maxBound] = NWI_DOMAIN;
  const candidates: Array<{ x: number; y: number }> = [];

  const yAtMinX = intercept + slope * minBound;
  if (yAtMinX >= minBound && yAtMinX <= maxBound) {
    candidates.push({ x: minBound, y: yAtMinX });
  }

  const yAtMaxX = intercept + slope * maxBound;
  if (yAtMaxX >= minBound && yAtMaxX <= maxBound) {
    candidates.push({ x: maxBound, y: yAtMaxX });
  }

  if (slope === 0) {
    if (intercept >= minBound && intercept <= maxBound) {
      candidates.push({ x: minBound, y: intercept });
      candidates.push({ x: maxBound, y: intercept });
    }
  } else {
    const xAtMinY = (minBound - intercept) / slope;
    if (xAtMinY >= minBound && xAtMinY <= maxBound) {
      candidates.push({ x: xAtMinY, y: minBound });
    }

    const xAtMaxY = (maxBound - intercept) / slope;
    if (xAtMaxY >= minBound && xAtMaxY <= maxBound) {
      candidates.push({ x: xAtMaxY, y: maxBound });
    }
  }

  const unique = candidates.filter(
    (point, index, arr) =>
      arr.findIndex((p) => Math.abs(p.x - point.x) < 1e-6 && Math.abs(p.y - point.y) < 1e-6) === index
  );

  if (unique.length < 2) {
    return null;
  }

  unique.sort((a, b) => (a.x === b.x ? a.y - b.y : a.x - b.x));
  return [unique[0], unique[unique.length - 1]];
}

function getTrendLineColor(componentKey: ComponentKey): string {
  return TREND_LINE_COLORS[componentKey];
}

export function ComponentCorrelationChart({ blockGroups }: ComponentCorrelationChartProps) {
  const [activeComponent, setActiveComponent] = useState<ComponentKey>("d2a");
  const [showTrendLine, setShowTrendLine] = useState<boolean>(true);

  const data = useMemo(
    () =>
      blockGroups
        .filter((bg) => bg.natwalkind != null)
        .map((bg) => ({
          nwi: bg.natwalkind!,
          d2a: bg.d2a_ranked,
          d2b: bg.d2b_ranked,
          d3b: bg.d3b_ranked,
          d4a: bg.d4a_ranked,
        }))
        .filter((d) => d.d2a != null || d.d2b != null || d.d3b != null || d.d4a != null),
    [blockGroups]
  );

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

  const correlations = useMemo(() => {
    const nwiValues = data.map((d) => d.nwi);
    return {
      d2a: calculateCorrelation(data.map((d) => d.d2a), nwiValues),
      d2b: calculateCorrelation(data.map((d) => d.d2b), nwiValues),
      d3b: calculateCorrelation(data.map((d) => d.d3b), nwiValues),
      d4a: calculateCorrelation(data.map((d) => d.d4a), nwiValues),
    };
  }, [data]);

  const selectedInfo = COMPONENT_INFO[`${activeComponent}_ranked` as keyof typeof COMPONENT_INFO];
  const selectedData = scatterSeriesByComponent[activeComponent];
  const selectedCorrelation = correlations[activeComponent];
  const selectedTrendLine = useMemo(() => buildTrendLine(selectedData), [selectedData]);
  const correlationDescriptor = getCorrelationDescriptor(selectedCorrelation);

  if (data.length === 0) {
    return <p>No data available for correlation analysis.</p>;
  }

  return (
    <ChartErrorBoundary chartName="Component Correlation Chart">
      <div className="correlation-charts">
        <div className="correlation-header">
          <div className="correlation-header__title-group">
            <p className="correlation-header__eyebrow">Focused relationship view</p>
            <h3>
              {formatComponentLabel(selectedInfo)} vs NWI
            </h3>
            <p className="correlation-header__hint">Switch components to compare trends quickly.</p>
          </div>
          <div className="correlation-header__metric" aria-live="polite">
            <span className="correlation-header__metric-label">Correlation (r)</span>
            <strong className="correlation-header__metric-value">{selectedCorrelation.toFixed(3)}</strong>
            <span className="correlation-header__metric-description">{correlationDescriptor}</span>
          </div>
        </div>
        <div className="correlation-controls">
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
          <button
            type="button"
            className={`correlation-trend-toggle ${showTrendLine ? "correlation-trend-toggle--active" : ""}`}
            aria-pressed={showTrendLine}
            onClick={() => setShowTrendLine((prev) => !prev)}
          >
            {showTrendLine ? "Trend line on" : "Trend line off"}
          </button>
        </div>
        <div className="correlation-chart-container" aria-label={`Scatter plot showing ${selectedInfo.shortLabel} versus NWI`}>
          <ResponsiveContainer width="100%" height={CHART_HEIGHTS.correlation}>
            <ScatterChart margin={CORRELATION_CHART_MARGINS}>
              <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 5" vertical={false} />
              <XAxis
                type="number"
                dataKey="nwi"
                name="NWI Score"
                height={CORRELATION_AXIS.xAxisHeight}
                tick={{ fontSize: 12, fill: "#4b5563" }}
                tickMargin={6}
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
                tick={{ fontSize: 12, fill: "#4b5563" }}
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
                contentStyle={{
                  borderRadius: 8,
                  border: "1px solid #d1d5db",
                  boxShadow: "0 6px 18px rgba(15, 23, 42, 0.08)",
                }}
                formatter={(value: number | undefined) => (value ?? 0).toFixed(2)}
                labelFormatter={(label: React.ReactNode) => `NWI: ${typeof label === "string" ? label : String(label ?? "")}`}
              />
              <Scatter
                name={formatComponentLabel(selectedInfo)}
                data={selectedData}
                fill={getComponentColor(activeComponent)}
                fillOpacity={0.78}
                stroke={getComponentColor(activeComponent)}
                strokeOpacity={0.24}
                legendType="none"
              />
              {showTrendLine && selectedTrendLine && (
                <ReferenceLine
                  segment={selectedTrendLine}
                  stroke={getTrendLineColor(activeComponent)}
                  strokeWidth={2.75}
                  strokeDasharray="4 3"
                  ifOverflow="extendDomain"
                />
              )}
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>
    </ChartErrorBoundary>
  );
}
