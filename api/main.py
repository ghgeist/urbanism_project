"""FastAPI entrypoint for the walkability API."""
from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.schemas import ErrorResponse, GeocodeResponse, HealthResponse, NwiSummaryResponse
from services.profile_summary import build_summary_from_coords, build_summary_from_location_query
from services.walkability import get_location

DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def _parse_cors_origins() -> list[str]:
    raw_origins = os.getenv("API_CORS_ORIGINS")
    if not raw_origins:
        return DEFAULT_CORS_ORIGINS
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins if origins else DEFAULT_CORS_ORIGINS


app = FastAPI(
    title="Urbanism Walkability API",
    version="0.1.0",
    description="API-first wrapper around EPA walkability summary metrics.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _error_payload(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return ErrorResponse(code=code, message=message, details=details).model_dump()


def _raise_api_error(status_code: int, code: str, message: str, details: Any = None) -> None:
    raise HTTPException(
        status_code=status_code,
        detail=_error_payload(code=code, message=message, details=details),
    )


@app.exception_handler(HTTPException)
def handle_http_exception(_, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        payload = _error_payload(
            code=str(detail["code"]),
            message=str(detail["message"]),
            details=detail.get("details"),
        )
    else:
        payload = _error_payload(code=f"http_{exc.status_code}", message=str(detail), details=None)
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
def handle_request_validation_error(_, exc: RequestValidationError):
    payload = _error_payload(
        code="validation_error",
        message="Request validation failed.",
        details=exc.errors(),
    )
    return JSONResponse(status_code=422, content=payload)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/geocode", response_model=GeocodeResponse, responses={404: {"model": ErrorResponse}})
def geocode(q: str = Query(min_length=1, description="Address, ZIP, or city query")) -> GeocodeResponse:
    location = get_location(q)
    if not location:
        _raise_api_error(
            status_code=404,
            code="location_not_found",
            message="Location not found.",
            details={"query": q},
        )
    lon, lat = location
    return GeocodeResponse(lat=lat, lon=lon, label=q)


@app.get(
    "/nwi/summary",
    response_model=NwiSummaryResponse,
    responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
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
        _raise_api_error(
            status_code=400,
            code="invalid_request",
            message=str(exc),
        )

    return NwiSummaryResponse.model_validate(summary)


@app.get(
    "/nwi/summary/by-query",
    response_model=NwiSummaryResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def nwi_summary_by_query(
    q: str = Query(min_length=1, description="Address, ZIP, or city query"),
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
        summary = build_summary_from_location_query(
            query=q,
            selected_radius_miles=selected_radius_miles,
            search_radius_miles=search_radius_miles,
            min_delta=min_delta,
            top_n=top_n,
        )
    except ValueError as exc:
        _raise_api_error(
            status_code=400,
            code="invalid_request",
            message=str(exc),
        )

    if summary is None:
        _raise_api_error(
            status_code=404,
            code="location_not_found",
            message="Location not found.",
            details={"query": q},
        )

    return NwiSummaryResponse.model_validate(summary)
