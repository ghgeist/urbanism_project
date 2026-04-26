"""Read-only WAS coverage and distribution summary.

Use after ``load_walkable_accessibility_score.py`` to confirm the table loaded,
measure direct GEOID overlap with the NWI table, and sanity-check the current
Amenity Richness buckets against the observed WAS 2019 distribution.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Allow running as a standalone script from the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from services.db import get_db_connection  # noqa: E402
from services.metrics import AMENITY_FULL_THRESHOLD, AMENITY_MODERATE_THRESHOLD  # noqa: E402


def _as_float(value: Any) -> float | None:
    """Convert DB numeric/decimal outputs to float for formatting."""
    if value is None:
        return None
    return float(value)


def fetch_was_distribution(conn) -> dict[str, Any]:
    """Return WAS row counts, NWI join coverage, percentiles, and bucket counts."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            WITH joined AS (
              SELECT w.geoid, w.was_2019, n.geoid20
              FROM walkable_accessibility_score w
              LEFT JOIN national_walkability_index n ON n.geoid20 = w.geoid
              WHERE w.was_2019 IS NOT NULL
            )
            SELECT
              COUNT(*) AS was_rows,
              COUNT(DISTINCT geoid) AS distinct_geoids,
              COUNT(geoid20) AS matched_rows,
              (COUNT(geoid20)::numeric / NULLIF(COUNT(DISTINCT geoid), 0)) * 100 AS join_rate_pct,
              MIN(was_2019),
              percentile_cont(0.25) WITHIN GROUP (ORDER BY was_2019),
              percentile_cont(0.5) WITHIN GROUP (ORDER BY was_2019),
              percentile_cont(0.75) WITHIN GROUP (ORDER BY was_2019),
              percentile_cont(0.9) WITHIN GROUP (ORDER BY was_2019),
              MAX(was_2019),
              COUNT(*) FILTER (WHERE was_2019 >= %s) AS full_count,
              COUNT(*) FILTER (WHERE was_2019 >= %s AND was_2019 < %s) AS moderate_count,
              COUNT(*) FILTER (WHERE was_2019 < %s) AS sparse_count
            FROM joined;
            """,
            (
                AMENITY_FULL_THRESHOLD,
                AMENITY_MODERATE_THRESHOLD,
                AMENITY_FULL_THRESHOLD,
                AMENITY_MODERATE_THRESHOLD,
            ),
        )
        row = cursor.fetchone()

    return {
        "was_rows": int(row[0] or 0),
        "distinct_geoids": int(row[1] or 0),
        "matched_rows": int(row[2] or 0),
        "join_rate_pct": _as_float(row[3]),
        "min": _as_float(row[4]),
        "p25": _as_float(row[5]),
        "median": _as_float(row[6]),
        "p75": _as_float(row[7]),
        "p90": _as_float(row[8]),
        "max": _as_float(row[9]),
        "full_count": int(row[10] or 0),
        "moderate_count": int(row[11] or 0),
        "sparse_count": int(row[12] or 0),
    }


def _format_number(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def format_summary(summary: dict[str, Any]) -> str:
    """Format the distribution summary for operator-facing CLI output."""
    total = summary["was_rows"] or 0

    def pct(count: int) -> str:
        if total == 0:
            return "n/a"
        return f"{(count / total) * 100:.1f}%"

    lines = [
        "WAS DISTRIBUTION SUMMARY (read-only)",
        "=" * 48,
        f"WAS rows:             {summary['was_rows']:,}",
        f"Distinct GEOIDs:      {summary['distinct_geoids']:,}",
        f"NWI-matched rows:     {summary['matched_rows']:,}",
        f"Naive join rate:      {_format_number(summary['join_rate_pct'])}%",
        "",
        "WAS 2019 distribution (0-30 scale)",
        f"min / p25 / median:  {_format_number(summary['min'])} / {_format_number(summary['p25'])} / {_format_number(summary['median'])}",
        f"p75 / p90 / max:     {_format_number(summary['p75'])} / {_format_number(summary['p90'])} / {_format_number(summary['max'])}",
        "",
        "Amenity Richness buckets using current thresholds",
        f"Full Amenity Access (>= {AMENITY_FULL_THRESHOLD:g}):      {summary['full_count']:,} ({pct(summary['full_count'])})",
        f"Moderate Amenity Access ({AMENITY_MODERATE_THRESHOLD:g}-{AMENITY_FULL_THRESHOLD:g}): {summary['moderate_count']:,} ({pct(summary['moderate_count'])})",
        f"Destination Sparse (< {AMENITY_MODERATE_THRESHOLD:g}):     {summary['sparse_count']:,} ({pct(summary['sparse_count'])})",
    ]
    return "\n".join(lines)


def main() -> int:
    conn = None
    try:
        conn = get_db_connection()
        summary = fetch_was_distribution(conn)
    except Exception as exc:
        print(f"ERROR: WAS distribution summary failed: {exc}")
        return 1
    finally:
        if conn is not None:
            conn.close()

    print(format_summary(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
