# Component Analysis Dashboard

The Component Analysis Dashboard provides deep insights into the four components that make up the National Walkability Index (NWI). This document describes the dashboard features, architecture, and usage.

## Overview

The dashboard is accessible at `/dashboard` and allows users to:
- Analyze component score distributions across block groups
- View correlations between components and overall NWI scores
- Compare component contributions to walkability
- Understand which components drive walkability in a given area

## Features

### 1. Component Distributions

**Visualization:** Histogram showing score distributions (1-20) for all four components

**Purpose:** Shows how component scores are distributed across block groups in the selected area. Helps identify if scores are clustered or spread out.

**Data Source:** Individual block group component scores from the API response

### 2. Component Correlations

**Visualization:** Scatter plot showing relationship between component scores and NWI scores

**Purpose:** Identifies which components are most strongly correlated with overall walkability. Includes:
- Interactive component selector to view one component at a time
- Correlation coefficients displayed for each component
- Visual scatter plot showing the relationship

**Data Source:** Block group component scores vs. NWI scores

**Correlation Calculation:** Uses Pearson correlation coefficient (ranges from -1 to +1)

### 3. Component Contribution

**Visualization:** Bar chart comparing average component scores to NWI mean

**Purpose:** Shows how each component's average compares to the overall NWI average. Includes a reference line showing the NWI mean for easy comparison.

**Data Source:** Aggregated component means from the API summary response

## Architecture

### Components

All dashboard components are located in `frontend/src/components/dashboard/`:

- `ComponentDistributionChart.tsx` - Histogram visualization
- `ComponentCorrelationChart.tsx` - Scatter plot with component selector
- `ComponentContributionChart.tsx` - Bar chart with NWI reference line
- `ChartErrorBoundary.tsx` - Error boundary wrapper for charts

### Shared Configuration

**`frontend/src/lib/chartConfig.ts`**
- Component color scheme (consistent across all charts)
- Chart margin and height configurations
- Helper functions for creating component data arrays

**`frontend/src/lib/componentLabels.ts`**
- Component labels and descriptions
- EPA-accurate naming conventions
- Single source of truth for component metadata

**`frontend/src/lib/correlation.ts`**
- Pearson correlation calculation utility
- Handles null values gracefully

### Error Handling

All chart components are wrapped with `ChartErrorBoundary` to:
- Prevent page crashes if Recharts encounters errors
- Display user-friendly error messages
- Log errors for debugging (in development mode)

### Accessibility

The dashboard includes:
- ARIA labels on all charts and interactive elements
- Keyboard navigation support
- Screen reader friendly component selector
- Semantic HTML structure

## Component Colors

The dashboard uses a consistent color scheme:

- **D2A (Employment and Household Mix):** `#8884d8` (Purple)
- **D2B (Employment Mix):** `#82ca9d` (Green)
- **D3B (Intersection Density):** `#ffc658` (Yellow)
- **D4A (Transit Proximity):** `#ff7300` (Orange)

Colors are defined in `frontend/src/lib/chartConfig.ts` and should be updated there if changes are needed.

## API Requirements

The dashboard requires component scores in the API response. The `block_groups` array must include:
- `d2a_ranked` - Employment and Household Mix score (1-20)
- `d2b_ranked` - Employment Mix score (1-20)
- `d3b_ranked` - Intersection Density score (1-20)
- `d4a_ranked` - Transit Proximity score (1-20)

These are included in the API response starting with schema version `2026-02-19-component-scores`.

## Usage

### Basic Usage

1. Navigate to `/dashboard`
2. Enter a location (address, ZIP code, or city)
3. Adjust the radius slider (0.1-3.0 miles)
4. Click "Analyze" to load component data
5. View the dashboard visualization sections

### URL Parameters

The dashboard uses the same URL parameter structure as the Explore page:
- `q` - Location query string
- `radius` - Search radius in miles

Example: `/dashboard?q=Cambridge,%20MA&radius=1.0`

## Future Enhancements

Potential improvements based on research findings:

1. **Health Outcomes Integration** - Correlate NWI components with health data
2. **Equity Analysis** - Overlay socioeconomic indicators
3. **Temporal Analysis** - Show changes over time (if historical data available)
4. **Multi-location Comparison** - Compare components across multiple locations
5. **Export Functionality** - Download charts as images or data as CSV

See `docs/research/nwi-analytics-dashboard-research.md` for detailed research and recommendations.

## Development Notes

### Adding a New Chart

1. Create component in `frontend/src/components/dashboard/`
2. Wrap with `ChartErrorBoundary`
3. Use colors from `chartConfig.ts`
4. Use component labels from `componentLabels.ts`
5. Add ARIA labels for accessibility
6. Add to `Dashboard.tsx` page

### Modifying Component Colors

Update `COMPONENT_COLORS` in `frontend/src/lib/chartConfig.ts`. All charts will automatically use the new colors.

### Testing

- Test with various locations (urban, suburban, rural)
- Test with different radius values
- Verify error boundaries catch Recharts errors
- Test keyboard navigation and screen reader compatibility
