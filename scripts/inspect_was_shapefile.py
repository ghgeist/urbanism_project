"""
Read-only inspection of the US_WAS_1997_2019 shapefile.

Reports:
- Columns + dtypes
- Row count
- CRS
- Candidate 2019 score column
- Sample rows (3)
- GEOID vintage detection + naive join rate against national_walkability_index.geoid20

This script does NOT write to the database. Run it before load_walkable_accessibility_score.py
so you can decide whether the naive GEOID join is good enough or whether a crosswalk is needed.

Usage (from repo root):
    python scripts/inspect_was_shapefile.py

Env vars honored:
    WAS_SHAPEFILE_PATH   Local path to the zip or unzipped .shp (default: US_WAS_1997_2019.shp.zip)
    PG* / DATABASE_URL   Standard DB connection vars, read via services.db
"""
from __future__ import annotations

import logging
import os
import sys
import tempfile
import zipfile
from pathlib import Path

# Allow running as a standalone script from the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import geopandas as gpd  # noqa: E402

from services.db import get_db_connection  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("inspect_was")

DEFAULT_SHAPEFILE_PATH = "US_WAS_1997_2019.shp.zip"


def _resolve_shapefile_source() -> Path:
    source = os.environ.get("WAS_SHAPEFILE_PATH", DEFAULT_SHAPEFILE_PATH)
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(
            f"Shapefile source not found: {path.resolve()}. "
            "Set WAS_SHAPEFILE_PATH or place US_WAS_1997_2019.shp.zip at the repo root."
        )
    return path


def _open_shapefile(path: Path, tmpdir: Path) -> gpd.GeoDataFrame:
    """Open a .shp or .shp.zip and return a GeoDataFrame. Uses tmpdir for unzipping."""
    if path.suffix.lower() == ".zip":
        log.info("Unzipping %s -> %s", path.name, tmpdir)
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmpdir)
        shps = list(tmpdir.rglob("*.shp"))
        if not shps:
            raise RuntimeError(f"No .shp file found inside {path}")
        if len(shps) > 1:
            log.warning("Multiple .shp files found; using first: %s", shps[0])
        return gpd.read_file(shps[0])
    return gpd.read_file(path)


def _detect_geoid_column(columns: list[str]) -> str | None:
    """Find the most likely GEOID column. Returns column name or None.

    The US_WAS_1997_2019 shapefile uses "ID" for the 12-digit block-group GEOID,
    so we include that in the preferred list.
    """
    preferred = ["GEOID20", "GEOID10", "GEOID", "BG_GEOID", "bg_geoid", "ID", "id"]
    lower_map = {c.lower(): c for c in columns}
    for cand in preferred:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    for c in columns:
        if "geoid" in c.lower():
            return c
    return None


def _detect_was_2019_column(columns: list[str]) -> str | None:
    """Find the most likely 2019 WAS score column."""
    preferred = ["WAS2019", "was2019", "WAS_2019", "was_2019", "WAS_19", "was_19"]
    lower_map = {c.lower(): c for c in columns}
    for cand in preferred:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    # Fallback: anything with "2019" in the name
    candidates_2019 = [c for c in columns if "2019" in c]
    if len(candidates_2019) == 1:
        return candidates_2019[0]
    if candidates_2019:
        log.warning("Multiple candidate 2019 columns: %s", candidates_2019)
        return candidates_2019[0]
    return None


def _infer_geoid_vintage(sample_values: list[str]) -> str:
    """Best-effort vintage guess. We cannot be certain from the string alone."""
    non_null = [str(v) for v in sample_values if v is not None and str(v).strip()]
    if not non_null:
        return "unknown (no non-null samples)"
    lengths = {len(v) for v in non_null}
    if lengths == {12}:
        return "12-digit block-group GEOID (vintage undetermined from string alone)"
    return f"variable length GEOIDs: {sorted(lengths)}"


def _probe_join_rate(geoid_values: list[str]) -> dict:
    """Compute naive string-join rate against national_walkability_index.geoid20."""
    sample = [str(v) for v in geoid_values[:10000] if v is not None]
    if not sample:
        return {"probed": 0, "matched": 0, "rate": None, "error": "no non-null GEOIDs"}
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        conn.set_session(readonly=True)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(DISTINCT geoid20) FROM national_walkability_index WHERE geoid20 = ANY(%s);",
            (sample,),
        )
        matched = cursor.fetchone()[0] or 0
        return {"probed": len(sample), "matched": matched, "rate": matched / len(sample)}
    except Exception as exc:
        return {"probed": len(sample), "matched": 0, "rate": None, "error": str(exc)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def main() -> int:
    try:
        shp_path = _resolve_shapefile_source()
    except FileNotFoundError as exc:
        log.error(str(exc))
        return 1

    log.info("=" * 70)
    log.info("WAS SHAPEFILE INSPECTION (read-only)")
    log.info("Source: %s (%.1f MB)", shp_path, shp_path.stat().st_size / 1024 / 1024)
    log.info("=" * 70)

    with tempfile.TemporaryDirectory(prefix="was_inspect_") as tmp:
        tmpdir = Path(tmp)
        gdf = _open_shapefile(shp_path, tmpdir)

        log.info("\n-- Shape --")
        log.info("rows: %d", len(gdf))
        log.info("CRS:  %s", gdf.crs)

        log.info("\n-- Columns (%d) --", len(gdf.columns))
        for col in gdf.columns:
            dtype = str(gdf[col].dtype)
            log.info("  %-20s  %s", col, dtype)

        geoid_col = _detect_geoid_column(list(gdf.columns))
        was_col = _detect_was_2019_column(list(gdf.columns))
        log.info("\n-- Detection --")
        log.info("GEOID column:    %s", geoid_col or "NOT FOUND")
        log.info("WAS 2019 column: %s", was_col or "NOT FOUND")

        if geoid_col:
            samples = gdf[geoid_col].head(5).tolist()
            log.info("GEOID vintage:   %s", _infer_geoid_vintage(gdf[geoid_col].tolist()))
            log.info("GEOID samples:   %s", samples)

        log.info("\n-- Sample rows (first 3) --")
        preview_cols = [c for c in gdf.columns if c != "geometry"][:10]
        try:
            log.info("\n%s", gdf[preview_cols].head(3).to_string())
        except Exception as exc:
            log.warning("Could not stringify preview: %s", exc)

        if geoid_col:
            log.info("\n-- Join-rate probe against national_walkability_index.geoid20 --")
            result = _probe_join_rate(gdf[geoid_col].tolist())
            if result.get("error"):
                log.error("Probe failed: %s", result["error"])
            else:
                rate_pct = (result["rate"] or 0) * 100
                log.info(
                    "Probed %d sample GEOIDs; %d matched (%.2f%% naive join rate)",
                    result["probed"],
                    result["matched"],
                    rate_pct,
                )

    log.info("\n%s", "=" * 70)
    log.info("INSPECTION COMPLETE. No data written.")
    log.info("%s", "=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
