"""Tests for framework-agnostic profile summary service."""
from __future__ import annotations

from unittest.mock import patch

import geopandas as gpd
import pytest
from shapely.geometry import Point

from services.profile_summary import SCHEMA_VERSION, build_summary_from_coords, build_summary_from_location_query


def _sample_gdf(include_dist: bool = True, include_was: bool = False) -> gpd.GeoDataFrame:
    data = {
        "geoid20": ["A", "B", "C"],
        "natwalkind": [10.0, 14.0, 18.0],
        "d2a_ranked": [9.0, 11.0, 13.0],
        "d2b_ranked": [8.0, 10.0, 12.0],
        "d3b_ranked": [7.0, 9.0, 11.0],
        "d4a_ranked": [5.0, 15.0, 19.0],
        "geometry": [
            Point(-83.92, 35.96).buffer(0.01),
            Point(-83.93, 35.97).buffer(0.01),
            Point(-83.94, 35.98).buffer(0.01),
        ],
    }
    if include_dist:
        data["dist_miles"] = [0.2, 0.8, 1.6]
    if include_was:
        data["was_2019"] = [6.0, 12.0, 24.0]
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


class TestBuildSummaryFromCoords:
    def test_returns_canonical_shape_and_values(self):
        full_gdf = _sample_gdf(include_dist=True)
        with patch("services.profile_summary.query_walkability_by_coords", return_value=full_gdf) as mock_query:
            result = build_summary_from_coords(
                lat=35.96,
                lon=-83.92,
                selected_radius_miles=1.0,
                search_radius_miles=2.0,
                min_delta=2.0,
            )

        mock_query.assert_called_once_with(-83.92, 35.96, 2.0, conn=None)
        assert result["schema_version"] == SCHEMA_VERSION
        assert result["origin"]["lat"] == pytest.approx(35.96)
        assert result["origin"]["lon"] == pytest.approx(-83.92)
        assert result["origin"]["label"] is None
        assert result["counts"]["selected_block_groups"] == 2
        assert result["counts"]["context_block_groups"] == 3

        assert result["nwi"]["mean"] == pytest.approx(12.0)
        assert result["nwi"]["min"] == pytest.approx(10.0)
        assert result["nwi"]["max"] == pytest.approx(14.0)
        assert result["nwi"]["spread"] == pytest.approx(4.0)

        assert result["components"]["employment_housing_mix_rank_mean"] == pytest.approx(10.0)
        assert result["components"]["employment_type_diversity_rank_mean"] == pytest.approx(9.0)
        assert result["components"]["intersection_density_rank_mean"] == pytest.approx(8.0)
        assert result["components"]["transit_proximity_rank_mean_proxy"] == pytest.approx(10.0)

        assert result["metrics"]["everyday_convenience"] == pytest.approx(12.0)
        assert result["metrics"]["transit_viability"] == pytest.approx(10.0)
        assert result["metrics"]["variation"] == pytest.approx(2.828427, rel=1e-5)

        assert result["upgrade_potential"]["found"] is True
        assert len(result["upgrade_potential"]["candidates"]) == 1
        assert result["upgrade_potential"]["candidates"][0]["geoid20"] == "C"

        # block_groups: 2 block groups fall within selected_radius_miles=1.0 (dist 0.2, 0.8).
        assert "block_groups" in result
        assert len(result["block_groups"]) == 2
        bg0 = result["block_groups"][0]
        assert bg0["geoid20"] == "A"
        assert bg0["natwalkind"] == pytest.approx(10.0)
        assert isinstance(bg0["geometry"], dict)
        assert "type" in bg0["geometry"]
        assert "coordinates" in bg0["geometry"]

    def test_defaults_search_radius_to_selected_radius(self):
        full_gdf = _sample_gdf(include_dist=True)
        with patch("services.profile_summary.query_walkability_by_coords", return_value=full_gdf) as mock_query:
            result = build_summary_from_coords(
                lat=35.96,
                lon=-83.92,
                selected_radius_miles=1.0,
                search_radius_miles=None,
                min_delta=2.0,
            )

        mock_query.assert_called_once_with(-83.92, 35.96, 1.0, conn=None)
        assert result["selected_radius_miles"] == pytest.approx(1.0)
        assert result["search_radius_miles"] == pytest.approx(1.0)

    def test_without_dist_miles_uses_full_context_as_selected(self):
        full_gdf = _sample_gdf(include_dist=False)
        with patch("services.profile_summary.query_walkability_by_coords", return_value=full_gdf):
            result = build_summary_from_coords(
                lat=35.96,
                lon=-83.92,
                selected_radius_miles=1.0,
                search_radius_miles=2.0,
                min_delta=2.0,
            )

        assert result["counts"]["selected_block_groups"] == 3
        assert result["counts"]["context_block_groups"] == 3

    def test_block_groups_all_geometries_serialize(self):
        """All block groups within the search radius get valid GeoJSON geometry dicts."""
        full_gdf = _sample_gdf(include_dist=True)
        with patch("services.profile_summary.query_walkability_by_coords", return_value=full_gdf):
            result = build_summary_from_coords(
                lat=35.96,
                lon=-83.92,
                selected_radius_miles=2.0,
                search_radius_miles=2.0,
                min_delta=2.0,
            )
        assert len(result["block_groups"]) == 3
        for bg in result["block_groups"]:
            assert isinstance(bg["geometry"], dict)
            assert "type" in bg["geometry"]
            assert "coordinates" in bg["geometry"]

    def test_block_groups_skips_none_geometry(self):
        """Rows with None geometry are excluded from block_groups rather than raising."""
        gdf = gpd.GeoDataFrame(
            {
                "geoid20": ["X", "Y"],
                "natwalkind": [10.0, 14.0],
                "d2a_ranked": [9.0, 11.0],
                "d2b_ranked": [8.0, 10.0],
                "d3b_ranked": [7.0, 9.0],
                "d4a_ranked": [5.0, 15.0],
                "geometry": [None, Point(-83.92, 35.96).buffer(0.01)],
                "dist_miles": [0.2, 0.8],
            },
            crs="EPSG:4326",
        )
        with patch("services.profile_summary.query_walkability_by_coords", return_value=gdf):
            result = build_summary_from_coords(
                lat=35.96,
                lon=-83.92,
                selected_radius_miles=2.0,
                search_radius_miles=2.0,
                min_delta=2.0,
            )
        assert len(result["block_groups"]) == 1
        assert result["block_groups"][0]["geoid20"] == "Y"
        # counts.selected_block_groups tracks serialized geometry count, so it
        # matches len(block_groups) even when rows are dropped for None geometry.
        assert result["counts"]["selected_block_groups"] == 1

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"lat": 120.0, "lon": -83.9, "selected_radius_miles": 1.0}, "Latitude"),
            ({"lat": 35.9, "lon": -190.0, "selected_radius_miles": 1.0}, "Longitude"),
            ({"lat": 35.9, "lon": -83.9, "selected_radius_miles": 0.0}, "selected_radius_miles"),
            (
                {
                    "lat": 35.9,
                    "lon": -83.9,
                    "selected_radius_miles": 2.0,
                    "search_radius_miles": 1.0,
                },
                "search_radius_miles",
            ),
        ],
    )
    def test_validates_inputs(self, kwargs, message):
        with pytest.raises(ValueError, match=message):
            build_summary_from_coords(**kwargs)


class TestWasIntegration:
    def test_was_fields_absent_gracefully_when_column_missing(self):
        """If the JOIN returned no was_2019 column (e.g. WAS table not loaded), response still builds."""
        full_gdf = _sample_gdf(include_dist=True, include_was=False)
        with patch("services.profile_summary.query_walkability_by_coords", return_value=full_gdf):
            result = build_summary_from_coords(
                lat=35.96,
                lon=-83.92,
                selected_radius_miles=1.0,
                search_radius_miles=2.0,
                min_delta=2.0,
            )
        assert result["was"] == {"mean": None, "min": None, "max": None, "spread": None}
        assert result["amenity_richness"]["value"] is None
        assert result["amenity_richness"]["label"] == "Unavailable"
        assert result["hollow_neighborhood"]["is_hollow"] is False
        # block_groups still render; was_2019 is None per feature
        for bg in result["block_groups"]:
            assert bg["was_2019"] is None

    def test_was_stats_computed_over_selected_only(self):
        """WAS stats reflect the selected-radius subset, matching NWI stats convention."""
        full_gdf = _sample_gdf(include_dist=True, include_was=True)
        # selected_radius=1.0 -> rows with dist<=1.0 (A:0.2, B:0.8) have was 6.0, 12.0
        with patch("services.profile_summary.query_walkability_by_coords", return_value=full_gdf):
            result = build_summary_from_coords(
                lat=35.96,
                lon=-83.92,
                selected_radius_miles=1.0,
                search_radius_miles=2.0,
                min_delta=2.0,
            )
        assert result["was"]["mean"] == pytest.approx(9.0)
        assert result["was"]["min"] == pytest.approx(6.0)
        assert result["was"]["max"] == pytest.approx(12.0)
        assert result["was"]["spread"] == pytest.approx(6.0)

        assert result["amenity_richness"]["value"] == pytest.approx(9.0)
        assert result["amenity_richness"]["label"] == "Destination Sparse"

        # Selected NWI mean = (10+14)/2 = 12 (>= hollow threshold 13? no), WAS mean = 9
        # NWI mean 12 < 13, so not hollow even though WAS is low.
        assert result["hollow_neighborhood"]["is_hollow"] is False

    def test_hollow_neighborhood_detected_when_high_nwi_low_was(self):
        """A high-NWI, low-WAS selection triggers the hollow signal."""
        gdf = gpd.GeoDataFrame(
            {
                "geoid20": ["A", "B"],
                "natwalkind": [15.0, 17.0],
                "d2a_ranked": [9.0, 11.0],
                "d2b_ranked": [8.0, 10.0],
                "d3b_ranked": [7.0, 9.0],
                "d4a_ranked": [5.0, 15.0],
                "was_2019": [3.0, 5.0],
                "geometry": [
                    Point(-83.92, 35.96).buffer(0.01),
                    Point(-83.93, 35.97).buffer(0.01),
                ],
                "dist_miles": [0.2, 0.5],
            },
            crs="EPSG:4326",
        )
        with patch("services.profile_summary.query_walkability_by_coords", return_value=gdf):
            result = build_summary_from_coords(
                lat=35.96,
                lon=-83.92,
                selected_radius_miles=1.0,
                search_radius_miles=1.0,
                min_delta=2.0,
            )
        assert result["hollow_neighborhood"]["is_hollow"] is True
        assert result["hollow_neighborhood"]["label"] == "Hollow Neighborhood"

    def test_block_group_was_2019_passes_through(self):
        """Per-block-group was_2019 values survive serialization."""
        full_gdf = _sample_gdf(include_dist=True, include_was=True)
        with patch("services.profile_summary.query_walkability_by_coords", return_value=full_gdf):
            result = build_summary_from_coords(
                lat=35.96,
                lon=-83.92,
                selected_radius_miles=2.0,
                search_radius_miles=2.0,
                min_delta=2.0,
            )
        was_by_geoid = {bg["geoid20"]: bg["was_2019"] for bg in result["block_groups"]}
        assert was_by_geoid["A"] == pytest.approx(6.0)
        assert was_by_geoid["B"] == pytest.approx(12.0)
        assert was_by_geoid["C"] == pytest.approx(24.0)


class TestBuildSummaryFromLocationQuery:
    def test_returns_none_when_geocode_fails(self):
        with patch("services.profile_summary.get_location", return_value=None):
            result = build_summary_from_location_query(
                query="Nowhere, ZZ",
                selected_radius_miles=1.0,
            )
        assert result is None

    def test_sets_origin_label(self):
        with patch("services.profile_summary.get_location", return_value=(-83.92, 35.96)):
            with patch("services.profile_summary.build_summary_from_coords", return_value={"origin": {"label": None}}):
                result = build_summary_from_location_query(
                    query="Knoxville, TN",
                    selected_radius_miles=1.0,
                )
        assert result is not None
        assert result["origin"]["label"] == "Knoxville, TN"
