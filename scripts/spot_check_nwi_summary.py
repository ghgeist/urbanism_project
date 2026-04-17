"""
Spot-check /nwi/summary values against the WAS source shapefile.

Runs the full summary pipeline (via FastAPI's TestClient, so no separate
server is required) for a small, fixed set of reference block groups and
diffs each response against the WAS shapefile. The reference set is a
curated mix of urban/rural and covered/uncovered locations so regressions
in the WAS load — row drops, GEOID truncation, rescaling bugs — show up
on a single run.

Usage (from repo root):

    python scripts/spot_check_nwi_summary.py                # full report
    python scripts/spot_check_nwi_summary.py --quiet        # one-line per case
    python scripts/spot_check_nwi_summary.py --radius 0.25  # override radius

Env:
    WAS_SHAPEFILE_PATH   Path to .shp or .shp.zip (default: repo root zip)
    PG* / DATABASE_URL   Standard DB connection (via services/db.py)

Exit codes:
    0 — every check passed
    1 — at least one API↔shapefile mismatch or edge-case failure
    2 — could not read shapefile / DB (setup problem, not a regression)
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import geopandas as gpd  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402
from services.db import get_db_connection  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("spot_check_nwi")

DEFAULT_SHAPEFILE_PATH = _REPO_ROOT / "US_WAS_1997_2019.shp.zip"
# WAS values are stored as NUMERIC(5, 2); the raw shapefile is float32.
# Allow one-count rounding slack per direction.
WAS_ABS_TOLERANCE = 0.011


@dataclass(frozen=True)
class Reference:
    label: str
    lat: float
    lon: float
    # Expected flags for this reference point; `None` means "don't check".
    expect_any_was: bool | None = True  # at least one block_group returns non-null was_2019
    expect_any_zero_was: bool | None = None  # at least one BG has was_2019 == 0
    # When True/False, ``_diff_one`` asserts ``hollow_neighborhood.is_hollow`` matches.
    # ``None`` skips (the harness still requires the hollow block and keys below).
    expect_hollow_possible: bool | None = None
    expect_missing_was_row: bool | None = None  # at least one BG returns was_2019 = null
    notes: str = ""


# Curated mix spanning urban/rural and covered/uncovered regions.
# Coordinates are centroid-ish approximations of real block groups seeded
# from the shapefile; they are intentionally hard-coded so a data-drop bug
# in the load produces a visible diff rather than a silent miss.
REFERENCES: tuple[Reference, ...] = (
    Reference(
        label="Bronx, NY (high-WAS urban)",
        lat=40.8207, lon=-73.8599,
        expect_any_was=True,
        expect_hollow_possible=False,
        notes="Expect mean WAS well above moderate threshold (~20+).",
    ),
    Reference(
        label="Chicago North Side (high-WAS urban)",
        lat=41.9484, lon=-87.6553,
        expect_any_was=True,
        expect_hollow_possible=False,
        notes="Wrigley Field area; dense retail.",
    ),
    Reference(
        label="Cambridge, MA (mixed suburban)",
        lat=42.3736, lon=-71.1097,
        expect_any_was=True,
        expect_hollow_possible=False,
        notes="Mix of tract-level values; good sanity for moderate band.",
    ),
    Reference(
        label="Helena, MT (rural mountain)",
        lat=46.5891, lon=-112.0391,
        expect_any_was=True,
        expect_any_zero_was=True,
        notes="Expect at least one zero-WAS block group nearby.",
    ),
    Reference(
        label="Chicago suburb zero-WAS BG (industrial park)",
        lat=41.65669, lon=-87.89122,
        expect_any_was=True,
        expect_any_zero_was=True,
        notes="Direct hit on BG 170318238011 (WAS=0) with dense NWI context nearby.",
    ),
    Reference(
        label="Texas water-tract NWI-only (missing WAS row)",
        lat=27.93, lon=-96.94,
        # No expectation on total WAS availability — this is specifically to
        # exercise the LEFT JOIN path where some selected BGs return
        # was_2019=null.
        expect_any_was=None,
        expect_missing_was_row=True,
        notes="NWI geoid 480079900000 has no matching WAS row.",
    ),
    Reference(
        label="Anchorage, AK (outside WAS coverage)",
        lat=61.2181, lon=-149.9003,
        expect_any_was=False,
        expect_hollow_possible=False,
        notes="WAS is continental US only; every BG should return was_2019=null.",
    ),
)


def _resolve_shapefile() -> Path:
    env_path = os.environ.get("WAS_SHAPEFILE_PATH", "").strip()
    path = Path(env_path) if env_path else DEFAULT_SHAPEFILE_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Shapefile not found: {path}. "
            "Set WAS_SHAPEFILE_PATH or place US_WAS_1997_2019.shp.zip at the repo root."
        )
    return path


def _load_shapefile(path: Path, tmpdir: Path) -> gpd.GeoDataFrame:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmpdir)
        shps = list(tmpdir.rglob("*.shp"))
        if not shps:
            raise RuntimeError(f"No .shp file found inside {path}")
        gdf = gpd.read_file(shps[0])
    else:
        gdf = gpd.read_file(path)
    # Normalize to the loader's contract: string ID, 12-digit, lookup map only.
    gdf["ID"] = gdf["ID"].astype(str).str.strip()
    return gdf[["ID", "WAS2019"]].copy()


def _bg_to_shapefile_value(shapefile_lookup: dict[str, float | None], geoid: str | None) -> float | None:
    """Return the shapefile WAS value for a 12-digit GEOID, or None if absent/NaN."""
    if not geoid:
        return None
    raw = shapefile_lookup.get(str(geoid).strip())
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value:  # NaN check without importing math
        return None
    return value


def _almost_equal(a: float | None, b: float | None) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(a - b) <= WAS_ABS_TOLERANCE


def _db_has_was_table() -> bool:
    """Sanity check: refuse to run if the WAS table is not loaded."""
    try:
        conn = get_db_connection()
    except Exception as exc:  # pragma: no cover — env-setup concern
        log.error("Cannot connect to DB: %s", exc)
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('walkable_accessibility_score') IS NOT NULL;")
            return bool(cur.fetchone()[0])
    finally:
        conn.close()


def _fetch_summary(client: TestClient, ref: Reference, radius: float) -> dict[str, Any]:
    params = {
        "lat": ref.lat,
        "lon": ref.lon,
        "selected_radius_miles": radius,
        "search_radius_miles": max(radius * 3, 1.5),
        "min_delta": 2.0,
        "top_n": 3,
    }
    response = client.get("/nwi/summary", params=params)
    response.raise_for_status()
    return response.json()


@dataclass
class CheckResult:
    label: str
    passed: bool
    messages: list[str]


def _diff_one(ref: Reference, payload: dict[str, Any], shapefile_lookup: dict[str, float | None]) -> CheckResult:
    messages: list[str] = []
    passed = True

    block_groups = payload.get("block_groups", [])
    counts = payload.get("counts", {})
    was_stats = payload.get("was") or {}
    hollow = payload.get("hollow_neighborhood")

    messages.append(
        f"  selected_block_groups={counts.get('selected_block_groups')}, "
        f"was.mean={was_stats.get('mean')}, nwi.mean={(payload.get('nwi') or {}).get('mean')}, "
        f"hollow={bool(hollow and hollow.get('is_hollow'))}"
    )

    nonnull_was = [bg for bg in block_groups if bg.get("was_2019") is not None]
    null_was = [bg for bg in block_groups if bg.get("was_2019") is None]
    zero_was = [bg for bg in nonnull_was if float(bg["was_2019"]) == 0.0]

    # Structural expectations
    if ref.expect_any_was is True and not nonnull_was:
        passed = False
        messages.append(
            f"  FAIL: expected at least one non-null was_2019 in {len(block_groups)} BGs; got none."
        )
    if ref.expect_any_was is False and nonnull_was:
        passed = False
        sample = [(bg.get("geoid20"), bg.get("was_2019")) for bg in nonnull_was[:3]]
        messages.append(
            f"  FAIL: expected all was_2019 to be null (outside WAS coverage); got {len(nonnull_was)} non-null. "
            f"Sample: {sample}"
        )
    if ref.expect_any_zero_was and not zero_was:
        passed = False
        messages.append("  FAIL: expected at least one was_2019 = 0.0 BG; got none.")
    if ref.expect_missing_was_row and not null_was:
        passed = False
        messages.append(
            f"  FAIL: expected at least one BG with missing WAS row (was_2019=null); "
            f"got {len(nonnull_was)} non-null out of {len(block_groups)}."
        )

    if ref.expect_hollow_possible is True:
        if not hollow or not hollow.get("is_hollow"):
            passed = False
            messages.append(
                "  FAIL: expected hollow_neighborhood.is_hollow true (aggregate NWI/WAS "
                f"per check_hollow_neighborhood); got hollow={hollow!r}."
            )
    if ref.expect_hollow_possible is False and hollow and hollow.get("is_hollow"):
        passed = False
        messages.append(
            "  FAIL: expected hollow_neighborhood.is_hollow false; got true "
            f"(hollow={hollow!r})."
        )

    # Per-row diff vs the shapefile source.
    mismatches: list[str] = []
    for bg in block_groups:
        geoid = bg.get("geoid20")
        api_value = bg.get("was_2019")
        shapefile_value = _bg_to_shapefile_value(shapefile_lookup, geoid)
        if api_value is None and shapefile_value is None:
            # Expected: BG not in shapefile => NWI-only LEFT JOIN => null.
            continue
        if shapefile_value is None and api_value is not None:
            mismatches.append(
                f"    GEOID {geoid}: API has {api_value}, shapefile has no row."
            )
            continue
        if api_value is None and shapefile_value is not None:
            # DB row missing although shapefile has the GEOID — a load drop.
            mismatches.append(
                f"    GEOID {geoid}: API has null, shapefile has {shapefile_value:.2f}."
            )
            continue
        if not _almost_equal(api_value, shapefile_value):
            mismatches.append(
                f"    GEOID {geoid}: API={api_value:.2f}, shapefile={shapefile_value:.2f}, "
                f"|diff|={abs(api_value - shapefile_value):.3f}"
            )

    if mismatches:
        passed = False
        messages.append(
            f"  FAIL: {len(mismatches)} block group(s) disagree with shapefile (tol={WAS_ABS_TOLERANCE}):"
        )
        # Cap output so a huge radius doesn't flood the log.
        messages.extend(mismatches[:10])
        if len(mismatches) > 10:
            messages.append(f"    ... and {len(mismatches) - 10} more")
    else:
        messages.append(f"  OK: {len(block_groups)} BGs agree with shapefile (tol={WAS_ABS_TOLERANCE}).")

    # Hollow-neighborhood block contract: the summary must always include
    # the block with its (is_hollow, thresholds) shape so the UI never has
    # to special-case a missing key.
    if hollow is None:
        passed = False
        messages.append("  FAIL: hollow_neighborhood block missing from response.")
    else:
        if "is_hollow" not in hollow or "nwi_threshold" not in hollow or "was_threshold" not in hollow:
            passed = False
            messages.append(f"  FAIL: hollow_neighborhood missing required fields: {hollow}")

    return CheckResult(label=ref.label, passed=passed, messages=messages)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--radius", type=float, default=0.5, help="Selected radius in miles (default: 0.5)")
    parser.add_argument("--quiet", action="store_true", help="One line per case; no per-BG detail unless failing")
    args = parser.parse_args()

    if not _db_has_was_table():
        log.error(
            "walkable_accessibility_score table is not present in the target database. "
            "Run `python scripts/load_walkable_accessibility_score.py` first."
        )
        return 2

    try:
        shapefile_path = _resolve_shapefile()
    except FileNotFoundError as exc:
        log.error(str(exc))
        return 2

    with tempfile.TemporaryDirectory(prefix="spot_check_was_") as tmp:
        tmpdir = Path(tmp)
        log.info("Loading shapefile %s ...", shapefile_path.name)
        gdf = _load_shapefile(shapefile_path, tmpdir)
        lookup: dict[str, float | None] = {}
        for geoid, was in zip(gdf["ID"], gdf["WAS2019"], strict=True):
            try:
                value = float(was) if was is not None else None
            except (TypeError, ValueError):
                value = None
            if value is not None and value != value:  # NaN
                value = None
            lookup[str(geoid)] = value
        log.info("Loaded %d GEOIDs from shapefile.", len(lookup))

        client = TestClient(app)

        log.info("Spot-checking %d reference points at radius=%.2f mi ...", len(REFERENCES), args.radius)
        results: list[CheckResult] = []
        for ref in REFERENCES:
            try:
                payload = _fetch_summary(client, ref, args.radius)
            except Exception as exc:  # pragma: no cover — caller wants raw detail
                results.append(CheckResult(label=ref.label, passed=False, messages=[f"  ERROR: {exc}"]))
                continue
            results.append(_diff_one(ref, payload, lookup))

    # Report
    fails = [r for r in results if not r.passed]
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        log.info("[%s] %s", status, r.label)
        if args.quiet and r.passed:
            continue
        for line in r.messages:
            log.info("%s", line)

    log.info("")
    log.info("%d/%d spot-checks passed.", len(results) - len(fails), len(results))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
