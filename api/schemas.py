"""Pydantic schemas for the FastAPI contract."""
from __future__ import annotations

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

