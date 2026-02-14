"""Unit tests for pure profile metric calculations."""

import geopandas as gpd
from shapely.geometry import Point

from services.metrics import (
    DEFAULT_ISLAND_HIGH_THRESHOLD,
    DEFAULT_ISLAND_LOW_THRESHOLD,
    check_walkable_island,
    compute_everyday_convenience,
    compute_full_profile,
    compute_transit_viability,
    compute_upgrade_potential,
    compute_variation,
)


def _gdf(rows):
    """Create a small GeoDataFrame with EPSG:4326 geometry for tests."""
    data = []
    for idx, row in enumerate(rows):
        item = dict(row)
        item.setdefault("geoid20", f"bg-{idx:03d}")
        item["geometry"] = Point(-83.9 + (idx * 0.01), 35.9 + (idx * 0.01))
        data.append(item)
    return gpd.GeoDataFrame(data, geometry="geometry", crs="EPSG:4326")


class TestCoreMetrics:
    def test_compute_everyday_convenience_mean(self):
        gdf = _gdf([{"natwalkind": 10}, {"natwalkind": 14}, {"natwalkind": 16}])
        assert compute_everyday_convenience(gdf) == 13.333333333333334

    def test_compute_everyday_convenience_handles_empty_and_nan(self):
        empty = gpd.GeoDataFrame(columns=["natwalkind", "geometry"], geometry="geometry", crs="EPSG:4326")
        assert compute_everyday_convenience(empty) is None

        all_nan = _gdf([{"natwalkind": None}, {"natwalkind": "bad"}])
        assert compute_everyday_convenience(all_nan) is None

    def test_compute_variation(self):
        gdf = _gdf([{"natwalkind": 10}, {"natwalkind": 14}, {"natwalkind": 16}])
        result = compute_variation(gdf)
        assert result is not None
        assert round(result, 6) == round(3.0550504633038935, 6)

    def test_compute_variation_single_row_and_all_nan_returns_none(self):
        single = _gdf([{"natwalkind": 12}])
        assert compute_variation(single) is None

        all_nan = _gdf([{"natwalkind": None}, {"natwalkind": "bad"}])
        assert compute_variation(all_nan) is None

    def test_compute_transit_viability(self):
        gdf = _gdf([{"d4a_ranked": 8}, {"d4a_ranked": 12}, {"d4a_ranked": 20}])
        assert compute_transit_viability(gdf) == 13.333333333333334

    def test_compute_transit_viability_empty_returns_none(self):
        gdf = _gdf([{"d4a_ranked": None}, {"d4a_ranked": "x"}])
        assert compute_transit_viability(gdf) is None


class TestUpgradePotential:
    def test_compute_upgrade_potential_filters_and_sorts(self):
        selected = _gdf(
            [
                {"geoid20": "A", "natwalkind": 8.0, "dist_miles": 0.2},
                {"geoid20": "B", "natwalkind": 10.0, "dist_miles": 0.7},
            ]
        )
        search = _gdf(
            [
                {"geoid20": "A", "natwalkind": 18.0, "dist_miles": 1.2},  # excluded by geoid
                {"geoid20": "C", "natwalkind": 11.5, "dist_miles": 1.0},  # delta 2.5
                {"geoid20": "D", "natwalkind": 13.0, "dist_miles": 2.0},  # delta 4.0
                {"geoid20": "E", "natwalkind": 15.0, "dist_miles": 6.0},  # outside radius
                {"geoid20": "F", "natwalkind": 10.1, "dist_miles": 1.5},  # below min_delta
            ]
        )
        result = compute_upgrade_potential(
            selected,
            search,
            min_delta=2.0,
            top_n=3,
            search_radius_miles=3.0,
        )

        assert result["found"] is True
        assert result["selected_mean_nwi"] == 9.0
        assert [candidate["geoid20"] for candidate in result["candidates"]] == ["D", "C"]
        assert result["candidates"][0]["delta_nwi"] == 4.0
        assert result["candidates"][0]["dist_miles"] == 2.0

    def test_compute_upgrade_potential_none_found_message(self):
        selected = _gdf([{"geoid20": "A", "natwalkind": 12.0, "dist_miles": 0.3}])
        search = _gdf([{"geoid20": "B", "natwalkind": 12.2, "dist_miles": 2.0}])

        result = compute_upgrade_potential(
            selected,
            search,
            min_delta=1.0,
            search_radius_miles=3.0,
        )

        assert result["found"] is False
        assert result["candidates"] == []
        assert result["message"] == "No improvement found within 3.0 miles."

    def test_compute_upgrade_potential_all_nan_baseline(self):
        selected = _gdf([{"natwalkind": None}, {"natwalkind": "x"}])
        search = _gdf([{"natwalkind": 20.0, "dist_miles": 1.0}])
        result = compute_upgrade_potential(selected, search, min_delta=2.0, search_radius_miles=3.0)
        assert result["found"] is False
        assert result["selected_mean_nwi"] is None


class TestIslandAndFullProfile:
    def test_walkable_island_default_thresholds(self):
        island = check_walkable_island(16.0, 10.0)
        assert island["is_island"] is True
        assert island["label"] == "Walkable Island"
        assert island["high_threshold"] == DEFAULT_ISLAND_HIGH_THRESHOLD
        assert island["low_threshold"] == DEFAULT_ISLAND_LOW_THRESHOLD

    def test_walkable_island_custom_thresholds(self):
        island = check_walkable_island(12.0, 11.0, high_threshold=11.5, low_threshold=11.2)
        assert island["is_island"] is True

    def test_compute_full_profile_has_expected_keys(self):
        selected = _gdf(
            [
                {"geoid20": "A", "natwalkind": 13.0, "d4a_ranked": 12.0, "dist_miles": 0.1},
                {"geoid20": "B", "natwalkind": 15.0, "d4a_ranked": 14.0, "dist_miles": 0.8},
            ]
        )
        context = _gdf(
            [
                {"geoid20": "A", "natwalkind": 13.0, "d4a_ranked": 12.0, "dist_miles": 0.1},
                {"geoid20": "B", "natwalkind": 15.0, "d4a_ranked": 14.0, "dist_miles": 0.8},
                {"geoid20": "C", "natwalkind": 18.0, "d4a_ranked": 18.0, "dist_miles": 2.5},
            ]
        )

        profile = compute_full_profile(
            selected_gdf=selected,
            context_gdf=context,
            origin_lon=-83.92,
            origin_lat=35.96,
            search_radius_miles=3.0,
            min_delta=2.0,
        )

        expected_keys = {
            "origin",
            "search_radius_miles",
            "selected_count",
            "context_count",
            "everyday_convenience",
            "selected_mean_nwi",
            "context_mean_nwi",
            "variation",
            "transit_viability",
            "upgrade_potential",
            "walkable_island",
        }
        assert expected_keys.issubset(set(profile.keys()))
        assert profile["origin"] == {"lon": -83.92, "lat": 35.96}

    def test_compute_full_profile_all_nan_nwi(self):
        selected = _gdf([{"natwalkind": None, "d4a_ranked": 10, "dist_miles": 0.2}])
        context = _gdf([{"natwalkind": None, "d4a_ranked": 15, "dist_miles": 1.5}])
        profile = compute_full_profile(
            selected,
            context,
            origin_lon=-83.92,
            origin_lat=35.96,
            search_radius_miles=3.0,
            min_delta=2.0,
        )
        assert profile["everyday_convenience"] is None
        assert profile["variation"] is None
        assert profile["upgrade_potential"]["found"] is False
