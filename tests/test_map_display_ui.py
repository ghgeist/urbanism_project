"""Focused tests for Streamlit UI helper functions in map_display."""

from unittest.mock import Mock, patch

import pandas as pd

from components.map_display import render_nearby_better_list, render_summary_cards


class TestRenderSummaryCards:
    def test_render_summary_cards_with_candidate(self):
        profile = {
            "everyday_convenience": 12.345,
            "transit_viability": 14.0,
            "variation": 2.5,
            "upgrade_potential": {
                "found": True,
                "candidates": [
                    {"delta_nwi": 3.0, "dist_miles": 1.5}
                ],
            },
        }
        cols = [Mock(), Mock(), Mock(), Mock()]
        with patch("components.map_display.st.columns", return_value=cols):
            render_summary_cards(profile)

        assert cols[0].metric.call_args.args[0] == "Everyday Convenience"
        assert cols[0].metric.call_args.args[1] == "12.35"
        assert cols[3].metric.call_args.args[0] == "Upgrade Potential"
        assert cols[3].metric.call_args.args[1] == "+3.00 at 1.50 mi"

    def test_render_summary_cards_none_found(self):
        profile = {
            "everyday_convenience": None,
            "transit_viability": None,
            "variation": None,
            "upgrade_potential": {
                "found": False,
                "candidates": [],
                "message": "No improvement found within 3.0 miles.",
            },
        }
        cols = [Mock(), Mock(), Mock(), Mock()]
        with patch("components.map_display.st.columns", return_value=cols):
            render_summary_cards(profile)

        assert cols[0].metric.call_args.args[1] == "N/A"
        assert cols[3].metric.call_args.args[1] == "None found"


class TestRenderNearbyBetterList:
    def test_render_nearby_better_list_none_found(self):
        profile = {"upgrade_potential": {"found": False, "message": "No improvement found within 3.0 miles."}}
        with patch("components.map_display.st.write") as mock_write:
            with patch("components.map_display.st.info") as mock_info:
                with patch("components.map_display.st.dataframe") as mock_df:
                    render_nearby_better_list(profile)

        mock_write.assert_called_once()
        mock_info.assert_called_once_with("No improvement found within 3.0 miles.")
        mock_df.assert_not_called()

    def test_render_nearby_better_list_table(self):
        profile = {
            "upgrade_potential": {
                "found": True,
                "candidates": [
                    {"geoid20": "A", "natwalkind": 15.0, "delta_nwi": 3.5, "dist_miles": 1.2},
                    {"geoid20": "B", "natwalkind": 14.0, "delta_nwi": 2.5, "dist_miles": 0.8},
                ],
            }
        }
        with patch("components.map_display.st.write"):
            with patch("components.map_display.st.info") as mock_info:
                with patch("components.map_display.st.dataframe") as mock_df:
                    render_nearby_better_list(profile)

        mock_info.assert_not_called()
        assert mock_df.call_count == 1
        df_arg = mock_df.call_args.args[0]
        assert isinstance(df_arg, pd.DataFrame)
        assert "Block Group ID" in df_arg.columns
        assert "NWI Improvement" in df_arg.columns
