/**
 * Error boundary for chart components to prevent crashes from Recharts errors.
 */

import { Component, type ReactNode } from "react";

interface ChartErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  chartName?: string;
}

interface ChartErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ChartErrorBoundary extends Component<ChartErrorBoundaryProps, ChartErrorBoundaryState> {
  constructor(props: ChartErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ChartErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: unknown) {
    // Log error for debugging (in production, you might want to send to error tracking service)
    console.error(`Chart error in ${this.props.chartName || "chart"}:`, error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="chart-error" role="alert" aria-live="polite">
            <p>
              <strong>Unable to display chart.</strong>
            </p>
            <p style={{ fontSize: "0.9rem", color: "#6b7280", marginTop: "0.5rem" }}>
              {this.props.chartName ? `Error loading ${this.props.chartName}.` : "An error occurred while rendering the chart."}
            </p>
            {import.meta.env.MODE === "development" && this.state.error && (
              <details style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
                <summary>Error details (development only)</summary>
                <pre style={{ marginTop: "0.5rem", padding: "0.5rem", background: "#f3f4f6", borderRadius: "4px", overflow: "auto" }}>
                  {this.state.error.toString()}
                </pre>
              </details>
            )}
          </div>
        )
      );
    }

    return this.props.children;
  }
}
