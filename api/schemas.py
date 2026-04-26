"""Pydantic schemas for the FastAPI contract."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# Literal unions derived from ``services.metrics.AMENITY_RICHNESS_LABELS`` and
# ``HOLLOW_NEIGHBORHOOD_LABEL``. The schema deliberately hard-codes the strings
# so the wire contract stays resilient to accidental renames; a contract test
# enforces that these match the runtime constants.
AmenityRichnessLabel = Literal[
    "Full Amenity Access",
    "Moderate Amenity Access",
    "Destination Sparse",
    "Unavailable",
]
HollowNeighborhoodLabel = Literal["Hollow Neighborhood"]
UpgradePotentialMode = Literal["nwi_and_was", "nwi_only"]


class HealthResponse(BaseModel):
    status: str = Field(description="Service health status.")


class GeocodeResponse(BaseModel):
    lat: float
    lon: float
    label: str


class Counts(BaseModel):
    selected_block_groups: int
    context_block_groups: int


class NwiStats(BaseModel):
    mean: float | None
    min: float | None
    max: float | None
    spread: float | None


class WasStats(BaseModel):
    """Aggregate Walkable Accessibility Score (WAS, 0-30) stats over selected block groups.

    All fields are optional so clients can render "unavailable" states when the
    WAS table is not loaded or no block groups in the selected area have WAS data.
    """

    mean: float | None
    min: float | None
    max: float | None
    spread: float | None


class AmenityRichness(BaseModel):
    """Human-readable interpretation of the mean WAS score."""

    value: float | None
    label: AmenityRichnessLabel


class HollowNeighborhood(BaseModel):
    """Hollow Neighborhood signal: high NWI + low WAS = walkable bones, few destinations."""

    is_hollow: bool
    label: HollowNeighborhoodLabel | None
    nwi_threshold: float
    was_threshold: float


class Components(BaseModel):
    employment_housing_mix_rank_mean: float | None
    employment_type_diversity_rank_mean: float | None
    intersection_density_rank_mean: float | None
    transit_proximity_rank_mean_proxy: float | None


class Metrics(BaseModel):
    everyday_convenience: float | None
    variation: float | None
    transit_viability: float | None


class BlockGroupFeature(BaseModel):
    geoid20: str | None
    natwalkind: float | None
    d2a_ranked: float | None  # Employment and Household Mix
    d2b_ranked: float | None  # Employment Mix
    d3b_ranked: float | None  # Street Intersection Density
    d4a_ranked: float | None  # Proximity to Transit Stops
    was_2019: float | None = None  # Walkable Accessibility Score 2019 (0-30), None if unavailable
    geometry: dict[str, Any]  # GeoJSON geometry object (type + coordinates)


class UpgradeCandidate(BaseModel):
    geoid20: str | None
    natwalkind: float | None
    was_2019: float | None = None
    dist_miles: float | None
    delta_nwi: float | None
    delta_was: float | None = None


class UpgradePotential(BaseModel):
    found: bool
    candidates: list[UpgradeCandidate]
    selected_mean_nwi: float | None
    selected_mean_was: float | None = None
    min_delta_was: float = 2.0
    mode: UpgradePotentialMode = "nwi_only"
    message: str


class WalkableIsland(BaseModel):
    is_island: bool
    label: str | None
    high_threshold: float
    low_threshold: float


class Origin(BaseModel):
    lat: float
    lon: float
    label: str | None = None


class NwiSummaryResponse(BaseModel):
    schema_version: str
    origin: Origin
    selected_radius_miles: float
    search_radius_miles: float
    min_delta: float
    counts: Counts
    nwi: NwiStats
    was: WasStats | None = None
    components: Components
    metrics: Metrics
    amenity_richness: AmenityRichness | None = None
    upgrade_potential: UpgradePotential
    walkable_island: WalkableIsland
    hollow_neighborhood: HollowNeighborhood | None = None
    block_groups: list[BlockGroupFeature] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """API error payload. Keep canonical codes in sync with frontend API_ERROR_MESSAGES.

    Canonical codes used by this API:
    - location_not_found: geocode or summary-by-query could not resolve the location.
    - invalid_request: summary params invalid or business-rule failure (e.g. empty query).
    - validation_error: request body/query validation failed (e.g. 422).
    - internal_error: unhandled server error (generic 500).
    - service_unavailable: database temporarily unavailable (503).

    Unhandled HTTPExceptions are serialized with code="http_<status>" (e.g. http_404).
    Frontend maps http_404 and http_422 to the same copy as location_not_found and validation_error.
    """

    code: str
    message: str
    details: Any | None = None
