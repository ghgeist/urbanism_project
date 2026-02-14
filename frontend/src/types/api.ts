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
  components: Components;
  metrics: Metrics;
  upgrade_potential: UpgradePotential;
  walkable_island: WalkableIsland;
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
