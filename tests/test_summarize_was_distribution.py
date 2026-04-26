from scripts.summarize_was_distribution import format_summary


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
