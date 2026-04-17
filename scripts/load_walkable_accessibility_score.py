"""
Load the WAS 2019 snapshot from the US_WAS_1997_2019 shapefile into PostGIS.

Runs locally and writes over the wire to the remote Replit/Neon Postgres using the
existing PG* or DATABASE_URL env vars (same ones used by services/db.py).

Safety:
- Pre-flight prints target host + database + row count and requires confirmation
  before DROP/CREATE/INSERT. Set WAS_LOADER_CONFIRM=1 or pass --yes to skip the prompt.
- Uses DROP TABLE IF EXISTS + fresh load (idempotent). Re-runs start from scratch.

Usage (from repo root):
    python scripts/load_walkable_accessibility_score.py            # interactive confirm
    python scripts/load_walkable_accessibility_score.py --yes      # skip prompt
    WAS_LOADER_CONFIRM=1 python scripts/load_walkable_accessibility_score.py

Env vars:
    WAS_SHAPEFILE_PATH       Path to .shp or .shp.zip (default: US_WAS_1997_2019.shp.zip)
    WAS_SHAPEFILE_URL        Optional download URL; if set, downloads into a temp file
    WAS_LOADER_CONFIRM=1     Skip the interactive confirmation prompt
    PG* / DATABASE_URL       DB connection (via services/db.py)
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

# Allow running as a standalone script from the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import geopandas as gpd  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from tqdm import tqdm  # noqa: E402

from services.db import get_db_connection, get_pg_env  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("load_was")

DEFAULT_SHAPEFILE_PATH = "US_WAS_1997_2019.shp.zip"
TABLE_NAME = "walkable_accessibility_score"
CHUNK_SIZE = 1000

# Source shapefile column names (confirmed via scripts/inspect_was_shapefile.py).
SRC_GEOID_COL = "ID"
SRC_WAS_2019_COL = "WAS2019"


def _resolve_shapefile_source(tmpdir: Path) -> Path:
    """Return path to the .zip or .shp on disk, downloading if needed."""
    url = os.environ.get("WAS_SHAPEFILE_URL", "").strip()
    if url:
        log.info("Downloading shapefile from %s", url)
        target = tmpdir / "US_WAS_download.shp.zip"
        urllib.request.urlretrieve(url, target)
        log.info("Downloaded to %s (%.1f MB)", target, target.stat().st_size / 1024 / 1024)
        return target

    local = Path(os.environ.get("WAS_SHAPEFILE_PATH", DEFAULT_SHAPEFILE_PATH))
    if not local.exists():
        raise FileNotFoundError(
            f"Shapefile not found at {local.resolve()}. "
            "Set WAS_SHAPEFILE_PATH or WAS_SHAPEFILE_URL, or place US_WAS_1997_2019.shp.zip "
            "at the repo root."
        )
    return local


def _open_shapefile(source: Path, tmpdir: Path) -> gpd.GeoDataFrame:
    """Open a .shp or .shp.zip into a GeoDataFrame."""
    if source.suffix.lower() == ".zip":
        log.info("Unzipping %s -> %s", source.name, tmpdir)
        with zipfile.ZipFile(source) as zf:
            zf.extractall(tmpdir)
        shps = list(tmpdir.rglob("*.shp"))
        if not shps:
            raise RuntimeError(f"No .shp file found inside {source}")
        if len(shps) > 1:
            log.warning("Multiple .shp files found; using %s", shps[0])
        return gpd.read_file(shps[0])
    return gpd.read_file(source)


def _db_label() -> str:
    """Return a non-sensitive identifier of the target DB for the confirmation prompt."""
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if db_url:
        try:
            from urllib.parse import urlparse

            parsed = urlparse(db_url)
            host = parsed.hostname or "<unknown>"
            db = (parsed.path or "/").lstrip("/") or "<unknown>"
            return f"DATABASE_URL host={host} database={db}"
        except Exception:
            return "DATABASE_URL (unparseable)"
    try:
        env = get_pg_env()
        return f"PGHOST={env['host']} PGDATABASE={env['database']} PGUSER={env['user']}"
    except EnvironmentError as exc:
        raise SystemExit(f"Database credentials not configured: {exc}") from exc


def _confirm_or_exit(summary: str, auto_yes: bool) -> None:
    """Require user confirmation unless auto_yes is set."""
    if auto_yes or os.environ.get("WAS_LOADER_CONFIRM") == "1":
        log.info("Auto-confirming: %s", summary)
        return
    log.info("%s", summary)
    # Avoid input() footgun in automated environments — refuse to run without --yes
    # unless stdin is a real TTY.
    if not sys.stdin.isatty():
        raise SystemExit(
            "Not running in a TTY and --yes / WAS_LOADER_CONFIRM=1 was not set. "
            "Aborting without writing to the database."
        )
    answer = input("Proceed with DROP + fresh load? [y/N]: ").strip().lower()
    if answer not in ("y", "yes"):
        raise SystemExit("Aborted by user.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="Skip the interactive confirmation prompt")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="was_load_") as tmp:
        tmpdir = Path(tmp)

        source_path = _resolve_shapefile_source(tmpdir)
        log.info("Reading shapefile: %s (%.1f MB)", source_path, source_path.stat().st_size / 1024 / 1024)
        gdf = _open_shapefile(source_path, tmpdir)
        log.info("Loaded %d rows, CRS=%s", len(gdf), gdf.crs)

        missing = [c for c in (SRC_GEOID_COL, SRC_WAS_2019_COL) if c not in gdf.columns]
        if missing:
            raise SystemExit(
                f"Source shapefile missing expected column(s): {missing}. "
                "Re-run scripts/inspect_was_shapefile.py to verify schema."
            )

        log.info("Projecting geometry to EPSG:4326...")
        gdf = gdf.to_crs(epsg=4326)

        log.info("Selecting columns and normalizing types...")
        trimmed = gdf[[SRC_GEOID_COL, SRC_WAS_2019_COL, "geometry"]].copy()
        trimmed = trimmed.rename(columns={SRC_GEOID_COL: "geoid", SRC_WAS_2019_COL: "was_2019"})
        trimmed["geoid"] = trimmed["geoid"].astype(str).str.strip()
        before = len(trimmed)
        trimmed = trimmed.dropna(subset=["geoid"])
        trimmed = trimmed[trimmed["geoid"].str.len() > 0]
        dropped = before - len(trimmed)
        if dropped:
            log.info("Dropped %d rows with missing/empty GEOID", dropped)

        trimmed = trimmed.drop_duplicates(subset=["geoid"], keep="first")
        log.info("Final row count after de-dupe: %d", len(trimmed))

        db_label = _db_label()
        summary = (
            f"About to DROP + recreate table `{TABLE_NAME}` and insert {len(trimmed)} rows.\n"
            f"Target: {db_label}"
        )
        _confirm_or_exit(summary, auto_yes=args.yes)

        _execute_load(trimmed)

    log.info("Load complete.")
    return 0


def _execute_load(gdf: gpd.GeoDataFrame) -> None:
    """Drop/create the target table and stream rows in chunks."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            log.info("Enabling PostGIS extension (no-op if already enabled)...")
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

            log.info("Dropping existing %s if present...", TABLE_NAME)
            cur.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")

            log.info("Creating %s...", TABLE_NAME)
            cur.execute(
                f"""
                CREATE TABLE {TABLE_NAME} (
                    geoid VARCHAR(12) PRIMARY KEY,
                    was_2019 NUMERIC(5, 2),
                    geometry GEOMETRY(Geometry, 4326)
                );
                """
            )
        conn.commit()
    finally:
        conn.close()

    engine = _build_engine()
    try:
        total_chunks = (len(gdf) + CHUNK_SIZE - 1) // CHUNK_SIZE
        log.info("Inserting %d rows in %d chunks of %d...", len(gdf), total_chunks, CHUNK_SIZE)
        with tqdm(total=total_chunks, desc="WAS insert", unit="chunk") as pbar:
            for i in range(total_chunks):
                chunk = gdf.iloc[i * CHUNK_SIZE : (i + 1) * CHUNK_SIZE]
                chunk.to_postgis(TABLE_NAME, engine, if_exists="append", index=False)
                pbar.update(1)
    finally:
        engine.dispose()

    # Post-load: spatial index + ANALYZE for planner.
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            log.info("Creating spatial index was_geom_idx...")
            cur.execute(f"CREATE INDEX IF NOT EXISTS was_geom_idx ON {TABLE_NAME} USING GIST (geometry);")
            log.info("Running ANALYZE %s...", TABLE_NAME)
            cur.execute(f"ANALYZE {TABLE_NAME};")
        conn.commit()
    finally:
        conn.close()


def _build_engine():
    """Create a SQLAlchemy engine using the same env-var contract as services/db.py."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        # SQLAlchemy wants 'postgresql://' not 'postgres://'.
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        return create_engine(url)
    env = get_pg_env()
    return create_engine(
        f"postgresql://{env['user']}:{env['password']}@{env['host']}:{env['port']}/{env['database']}"
    )


if __name__ == "__main__":
    sys.exit(main())
