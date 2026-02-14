"""Focused tests for Streamlit UI helper functions in map_display."""

from unittest.mock import MagicMock, patch

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
        cols = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        with patch("components.map_display.st.columns", return_value=cols):
            with patch("components.map_display.st.metric") as mock_metric:
                with patch("components.map_display.st.caption") as mock_caption:
                    render_summary_cards(profile)

        # Check Everyday Convenience
        everyday_calls = [c for c in mock_metric.call_args_list if len(c.args) >= 2 and c.args[0] == "Everyday Convenience"]
        assert len(everyday_calls) == 1
        assert everyday_calls[0].args[1] == "12.35"
        
        # Check Upgrade Potential metric value (now just the delta)
        upgrade_calls = [c for c in mock_metric.call_args_list if len(c.args) >= 2 and c.args[0] == "Upgrade Potential"]
        assert len(upgrade_calls) == 1
        assert upgrade_calls[0].args[1] == "+3.0"
        
        # Check caption for context
        # Captions called: "Transit proximity...", "Dispersion...", "1.5 mi away"
        caption_args = [c.args[0] for c in mock_caption.call_args_list]
        assert "1.5 mi away" in caption_args

    def test_render_summary_cards_multiple_candidates_shows_best_nearby(self):
        profile = {
            "everyday_convenience": 10.0,
            "transit_viability": 14.0,
            "variation": 2.5,
            "upgrade_potential": {
                "found": True,
                "candidates": [
                    {"delta_nwi": 4.6, "dist_miles": 0.4},
                    {"delta_nwi": 3.0, "dist_miles": 1.2},
                ],
            },
        }
        cols = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        with patch("components.map_display.st.columns", return_value=cols):
            with patch("components.map_display.st.metric") as mock_metric:
                with patch("components.map_display.st.caption") as mock_caption:
                    render_summary_cards(profile)

        upgrade_calls = [c for c in mock_metric.call_args_list if len(c.args) >= 2 and c.args[0] == "Upgrade Potential"]
        assert len(upgrade_calls) == 1
        assert upgrade_calls[0].args[1] == "+4.6"
        
        caption_args = [c.args[0] for c in mock_caption.call_args_list]
        assert "Best nearby (0.4 mi)" in caption_args

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
        cols = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        with patch("components.map_display.st.columns", return_value=cols):
            with patch("components.map_display.st.metric") as mock_metric:
                render_summary_cards(profile)

        # Check Everyday Convenience
        everyday_calls = [c for c in mock_metric.call_args_list if len(c.args) >= 2 and c.args[0] == "Everyday Convenience"]
        assert len(everyday_calls) == 1
        assert everyday_calls[0].args[1] == "N/A"

        # Check Upgrade Potential
        upgrade_calls = [c for c in mock_metric.call_args_list if len(c.args) >= 2 and c.args[0] == "Upgrade Potential"]
        assert len(upgrade_calls) == 1
        assert upgrade_calls[0].args[1] == "None found"


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
