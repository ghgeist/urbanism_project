---
created: 2026-02-14
---
# Slack Surface Explorer – Product Plan

## 1. Product Repositioning

The current repository demonstrates a clean geospatial pipeline around the EPA National Walkability Index (NWI), including spatial indexing, PostGIS queries, buffering, and component inspection.

The next evolution is not "more visualization." It is turning this capability into a decision-support tool.

New positioning:

> A neighborhood comparison tool that helps people understand how everyday convenience and flexibility change across space.

This reframes the project from data exploration to applied tradeoff modeling.

---

## 2. Problem Statement

Most location decisions over-focus on price per square foot.

What is often missing:

* How much daily life depends on driving
* How much coordination effort is required
* Whether nearby alternatives materially change that burden

This tool helps surface those hidden differences.

---

## 3. Core Product Thesis

Neighborhoods store flexibility in different ways.

Some rely heavily on:

* Private space
* Car access
* Predictable routines

Others rely more on:

* Proximity
* Street connectivity
* Mixed land use

The goal is not to rank moral superiority.
It is to make tradeoffs visible.

---

## 4. What the Tool Actually Does

For a selected address and radius:

1. Calculates average National Walkability Index (NWI)
2. Surfaces component drivers (land-use mix, employment mix, connectivity, transit)
3. Reports Transit Viability signal (based strictly on the EPA distance-to-transit component `d4a_ranked`)
4. Measures score variance within radius (stability vs variation)
5. Identifies nearby block groups within X miles that materially improve NWI

The final output is a structured internal "Slack Profile" (modeling term), not just a map.

**Note:** “Slack” is an internal modeling concept referring to flexibility. It is not intended as the public-facing product name.

---

## 5. Formal Metric Definitions (Spec-Level)

All metrics must be mathematically defined and reproducible.

**Everyday Convenience**
= mean(`natwalkind`) across all block groups intersecting the selected radius.

Higher values indicate greater proximity-based walkability according to the EPA National Walkability Index. This does not imply superior lifestyle outcomes or moral preference.

**Variation (Dispersion)**
= standard deviation of `natwalkind` across block groups within the selected radius.

This measures dispersion only. It does not imply risk, quality, desirability, or instability.

Higher dispersion indicates greater differences in walkability within the radius. Lower dispersion indicates more uniform walkability across the radius.

**Transit Viability Signal**
= mean(`d4a_ranked`) within the selected radius.

This reflects the EPA distance-to-transit component only. It does not measure total car dependence or household vehicle ownership.

**Upgrade Potential**
A candidate location qualifies as “better” only if:

candidate_mean_NWI - selected_mean_NWI >= min_delta
AND
geographic_distance <= search_radius

Where:

selected_mean_NWI = mean(`natwalkind`) within the originally selected radius.

No composite scoring or hidden weighting is permitted.

If no candidate meets the delta criteria within the search radius, the system must explicitly return: “No improvement found within X miles.”

**Walkable Island Check**
If:

selected_mean_NWI >= high_threshold
AND
radius_mean_NWI <= low_threshold

Then label as: “Walkable Island” (high local score surrounded by lower-scoring context).

Thresholds must be defined empirically or parameterized, not hardcoded without justification.

---

## 6. UI Pattern and Interaction Model

The interface should reinforce analytical clarity and interpretive restraint.

### Primary Layout Hierarchy

The UI must prioritize metrics over map visuals.

**Top Section: Profile Summary (Primary Focus)**

Four horizontally aligned summary cards:

1. Everyday Convenience (mean NWI)
2. Transit Viability (mean `d4a_ranked`)
3. Variation (stddev of NWI)
4. Upgrade Potential (nearest qualifying improvement or explicit "none found")

Each card must include:

* Numeric value
* Neutral descriptor
* Tooltip tied directly to formal metric definition

No red/green moral color coding is permitted.

**Middle Section: Controls + Comparison**

* Address input
* Radius control
* Delta threshold control
* "Compare" toggle (side-by-side view)

Comparison view must render two profile summaries side-by-side with highlighted metric differences.

**Bottom Section: Spatial Context**

* Map (evidence layer, not headline)
* Ranked nearby-better list
* Click interaction highlights geometry

The map supports interpretation but does not dominate the experience.

---

## 7. Bridge Phase (Before Full Frontend Migration)

To avoid a stalled rewrite:

1. Refactor service layer to return pure data (no UI rendering).
2. Implement Profile Summary cards inside current Streamlit app.
3. Add variation, nearby-better, and island check in Streamlit.
4. Validate that the output provides real insight.
5. Only then build FastAPI wrapper and migrate UI to React.

React migration should not begin until the data model is validated in the existing interface.

---

## 5. Slack Profile Output Structure

### Everyday Convenience

* NWI (average within radius)
* High / moderate / low interpretation

### Mobility Pattern

* Relative car dependence proxy
* Street connectivity signal

### Stability vs Variation

* How consistent the surrounding area is
* Whether better alternatives are close

### Upgrade Potential

* Top 3 nearby areas with improvement delta
* Distance to each

This transforms the tool into an actionable comparison engine.

---

## 6. Differentiation From Existing Tools

Unlike consumer "Walk Score" style products, this tool:

* Uses block-group level EPA data
* Exposes component-level drivers
* Allows radius-based aggregation
* Enables nearby improvement detection
* Prioritizes comparison over ranking

It is analytical rather than promotional.

---

## 7. Experiment Framing

This project functions as an experiment:

Hypothesis:
Higher NWI correlates with reduced coordination burden and increased daily flexibility.

The tool allows that hypothesis to be tested across:

* Suburban locations
* Walkable urban neighborhoods
* Hybrid edge zones

Unexpected results are considered signal, not failure.

---

## 8. Implementation Plan: FastAPI + React

This project will move from a Streamlit demo to a modular product stack.

### Backend: FastAPI (API-first)

**Purpose:** Provide a clean, stable interface for the frontend, and keep geospatial logic in one place.

**Phase 1 endpoints (minimum):**

* `GET /health`

  * Basic service check

* `GET /geocode?q=...`

  * Convert address / ZIP / city into `{ lat, lon, label }`
  * (Server-side geocoding avoids exposing rate limits and simplifies the UI.)

* `GET /nwi/summary?lat=...&lon=...&radius_miles=...`

  * Returns a single canonical response object:

    * Selected area (block group)
    * NWI stats within radius (mean / min / max / spread)
    * Component breakdown (land-use mix, employment mix, connectivity, transit)
    * “Stability vs variation” signal

**Optional Phase 2 endpoints:**

* `GET /nwi/nearby-better?lat=...&lon=...&search_miles=...&min_delta=...`

  * Returns ranked nearby areas with meaningful improvement

* `GET /nwi/compare?...`

  * A vs B comparison (or the frontend can call `/summary` twice and compare locally)

**Key guardrail:**
Define one canonical response schema (e.g., `NwiSummaryResponse`) and keep it stable.

### Frontend: React (product UX)

**Purpose:** Better map interactions, side-by-side comparison, and shareable links.

**Phase 1 pages:**

1. **Explore**

* Search input + radius slider
* Map view
* “Slack Profile” summary cards
* Data table (sortable)

2. **Compare**

* Two locations side-by-side
* Two summary panels
* Highlight differences (what improved, what got worse)

**Shareable state:**

* Location + radius should live in the URL query params so results can be shared.

### Map rendering

Start simple:

* React + Leaflet (fastest path, easy mental model)

Upgrade later only if needed:

* MapLibre GL / Mapbox GL for higher-performance interaction

### Deployment (practical)

* Backend: containerized FastAPI (Render/Fly.io/etc.)
* Frontend: Vercel/Netlify/static hosting
* Database: existing PostGIS

### Sequence (to avoid a rewrite spiral)

1. Define the response schema.
2. Stand up FastAPI returning that schema.
3. Build React UI that renders it.
4. Add comparison + nearby-better features.
5. Add caching after behavior is correct.

---

## 9. Metrics of Success

The tool succeeds if:

* A user understands their area in under 60 seconds.
* A user can identify at least one nearby alternative worth investigating.
* The output surfaces tradeoffs clearly without moral framing.
* The tool reveals at least one surprising geographic pattern.

---

## 10. Clear Public Description

A spatial comparison tool that uses the EPA’s National Walkability Index to help people see how everyday convenience, car dependence, and neighborhood flexibility vary across space — and how small geographic shifts can materially change daily life.

---

## 11. Interpretation Guardrails (To Prevent Model Drift)

Because this tool translates spatial data into human-readable summaries, strict guardrails are required to prevent overreach or hallucination.

### 1. All interpretations must map to explicit metrics

Every narrative statement must reference a measurable field:

* National Walkability Index (mean / min / max / spread)
* Named NWI component (land-use mix, employment mix, connectivity, transit)
* Distance-based delta calculations
* Standard deviation within radius

No interpretations may be generated without traceable metric grounding.

### 2. No causal claims

The tool must not claim:

* That higher NWI causes better health
* That higher NWI reduces coordination burden
* That commute mode mix predicts total car use

All outputs must remain descriptive, not causal.

### 3. Proxies must be labeled explicitly

* Commute mode mix = proxy for work-trip car dependence only
* Variance = dispersion of NWI within radius, not risk
* Connectivity = street intersection density, not safety or vibrancy

If a proxy is used, it must be labeled as such.

### 4. “Nearby Better” must be mathematically defined

A location qualifies as “better” only if:

candidate_mean_NWI - selected_mean_NWI >= min_delta
AND
geographic_distance <= search_radius

No hidden weighting, composite scoring, or subjective ranking.

### 5. No moral framing

The system must not imply:

* Urban is superior
* Suburban is inferior
* Density is desirable

The purpose is to surface tradeoffs, not prescribe values.

### 6. Hypothesis status must remain explicit

Any reference to flexibility, coordination, or convenience must be framed as:

"Hypothesis under exploration" rather than established fact.

---

These guardrails ensure the tool remains analytical, transparent, and falsifiable rather than rhetorical.
