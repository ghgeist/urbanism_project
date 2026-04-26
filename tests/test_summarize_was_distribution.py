from unittest.mock import MagicMock, Mock

from scripts.summarize_was_distribution import fetch_was_distribution, format_summary


def test_fetch_was_distribution_maps_sql_row_to_summary_dict():
    cursor = Mock()
    cursor.fetchone.return_value = (
        215831,
        215831,
        199388,
        92.38,
        0.0,
        0.5,
        8.45,
        21.19,
        26.87,
        29.62,
        59318,
        41816,
        114697,
    )
    conn = Mock()
    conn.cursor.return_value = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor

    summary = fetch_was_distribution(conn)

    assert summary == {
        "was_rows": 215831,
        "distinct_geoids": 215831,
        "matched_rows": 199388,
        "join_rate_pct": 92.38,
        "min": 0.0,
        "p25": 0.5,
        "median": 8.45,
        "p75": 21.19,
        "p90": 26.87,
        "max": 29.62,
        "full_count": 59318,
        "moderate_count": 41816,
        "sparse_count": 114697,
    }
    cursor.execute.assert_called_once()


def test_format_summary_includes_join_rate_distribution_and_bucket_counts():
    summary = {
        "was_rows": 215831,
        "distinct_geoids": 215831,
        "matched_rows": 199388,
        "join_rate_pct": 92.38,
        "min": 0.0,
        "p25": 0.5,
        "median": 8.45,
        "p75": 21.19,
        "p90": 26.87,
        "max": 29.62,
        "full_count": 59318,
        "moderate_count": 41816,
        "sparse_count": 114697,
    }

    output = format_summary(summary)

    assert "Naive join rate:      92.38%" in output
    assert "min / p25 / median:  0.00 / 0.50 / 8.45" in output
    assert "Full Amenity Access (>= 20):      59,318 (27.5%)" in output
    assert "Destination Sparse (< 10):     114,697 (53.1%)" in output
