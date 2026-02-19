"""Pydantic schemas for the FastAPI contract."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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
    geometry: dict[str, Any]  # GeoJSON geometry object (type + coordinates)


class UpgradeCandidate(BaseModel):
    geoid20: str | None
    natwalkind: float | None
    dist_miles: float | None
    delta_nwi: float | None


class UpgradePotential(BaseModel):
    found: bool
    candidates: list[UpgradeCandidate]
    selected_mean_nwi: float | None
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
    components: Components
    metrics: Metrics
    upgrade_potential: UpgradePotential
    walkable_island: WalkableIsland
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
