"""FastAPI entrypoint for the walkability API."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from api.schemas import GeocodeResponse, HealthResponse, NwiSummaryResponse
from services.profile_summary import build_summary_from_coords
from services.walkability import get_location

app = FastAPI(
    title="Urbanism Walkability API",
    version="0.1.0",
    description="API-first wrapper around EPA walkability summary metrics.",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/geocode", response_model=GeocodeResponse)
def geocode(q: str = Query(min_length=1, description="Address, ZIP, or city query")) -> GeocodeResponse:
    location = get_location(q)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found.")
    lon, lat = location
    return GeocodeResponse(lat=lat, lon=lon, label=q)


@app.get("/nwi/summary", response_model=NwiSummaryResponse)
def nwi_summary(
    lat: float = Query(description="Latitude in decimal degrees"),
    lon: float = Query(description="Longitude in decimal degrees"),
    selected_radius_miles: float = Query(gt=0.0, description="Selected profile radius in miles"),
    search_radius_miles: float | None = Query(
        default=None,
        gt=0.0,
        description="Search radius in miles for context/upgrade detection",
    ),
    min_delta: float = Query(default=2.0, ge=0.0, description="Minimum NWI improvement threshold"),
    top_n: int = Query(default=3, ge=1, le=10, description="Maximum nearby-better candidates to return"),
) -> NwiSummaryResponse:
    try:
        summary = build_summary_from_coords(
            lat=lat,
            lon=lon,
            selected_radius_miles=selected_radius_miles,
            search_radius_miles=search_radius_miles,
            min_delta=min_delta,
            top_n=top_n,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return NwiSummaryResponse.model_validate(summary)

