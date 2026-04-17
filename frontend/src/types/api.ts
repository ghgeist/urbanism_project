/** Types matching the FastAPI NwiSummaryResponse contract. */

export interface Origin {
  lat: number;
  lon: number;
  label: string | null;
}

export interface Counts {
  selected_block_groups: number;
  context_block_groups: number;
}

export interface NwiStats {
  mean: number | null;
  min: number | null;
  max: number | null;
  spread: number | null;
}

/**
 * Aggregate Walkable Accessibility Score (WAS, 0-30) stats over the selected radius.
 * All fields are nullable — the server returns this block with all nulls when the
 * WAS table is not loaded or no selected block groups have WAS data.
 */
export interface WasStats {
  mean: number | null;
  min: number | null;
  max: number | null;
  spread: number | null;
}

/**
 * Amenity Richness labels. Must match ``AMENITY_RICHNESS_LABELS`` in
 * ``services/metrics.py`` and the ``AmenityRichnessLabel`` Literal in
 * ``api/schemas.py``.
 */
export type AmenityRichnessLabel =
  | "Full Amenity Access"
  | "Moderate Amenity Access"
  | "Destination Sparse"
  | "Unavailable";

/** Hollow Neighborhood banner label (singleton). */
export type HollowNeighborhoodLabel = "Hollow Neighborhood";

/** Human-readable interpretation of the mean WAS score. */
export interface AmenityRichness {
  value: number | null;
  label: AmenityRichnessLabel;
}

/** Hollow Neighborhood signal: high NWI + low WAS = walkable bones, few destinations. */
export interface HollowNeighborhood {
  is_hollow: boolean;
  label: HollowNeighborhoodLabel | null;
  nwi_threshold: number;
  was_threshold: number;
}

export interface Components {
  employment_housing_mix_rank_mean: number | null;
  employment_type_diversity_rank_mean: number | null;
  intersection_density_rank_mean: number | null;
  transit_proximity_rank_mean_proxy: number | null;
}

export interface Metrics {
  everyday_convenience: number | null;
  variation: number | null;
  transit_viability: number | null;
}

export interface BlockGroupFeature {
  geoid20: string | null;
  natwalkind: number | null;
  d2a_ranked: number | null; // Employment and Household Mix
  d2b_ranked: number | null; // Employment Mix
  d3b_ranked: number | null; // Street Intersection Density
  d4a_ranked: number | null; // Proximity to Transit Stops
  was_2019: number | null; // Walkable Accessibility Score 2019 (0-30), null if unavailable
  geometry: GeoJSON.Geometry;
}

export interface UpgradeCandidate {
  geoid20: string | null;
  natwalkind: number | null;
  dist_miles: number | null;
  delta_nwi: number | null;
}

export interface UpgradePotential {
  found: boolean;
  candidates: UpgradeCandidate[];
  selected_mean_nwi: number | null;
  message: string;
}

export interface WalkableIsland {
  is_island: boolean;
  label: string | null;
  high_threshold: number;
  low_threshold: number;
}

export interface NwiSummaryResponse {
  schema_version: string;
  origin: Origin;
  selected_radius_miles: number;
  search_radius_miles: number;
  min_delta: number;
  counts: Counts;
  nwi: NwiStats;
  was?: WasStats | null;
  components: Components;
  metrics: Metrics;
  amenity_richness?: AmenityRichness | null;
  upgrade_potential: UpgradePotential;
  walkable_island: WalkableIsland;
  hollow_neighborhood?: HollowNeighborhood | null;
  block_groups: BlockGroupFeature[];
}

export interface GeocodeResponse {
  lat: number;
  lon: number;
  label: string;
}

export interface ErrorResponse {
  code: string;
  message: string;
  details?: unknown;
}
