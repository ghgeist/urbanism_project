# Replit agent prompt — Load WAS 2019 into Postgres

Paste the block below into the Replit agent. It assumes `US_WAS_1997_2019.shp.zip` is already uploaded to the repo root in the Repl.

---

## Prompt to paste into the Replit agent

I need you to run a one-shot data ingest. The repo has a new script
`scripts/load_walkable_accessibility_score.py` that loads the Walkable
Accessibility Score (WAS) 2019 snapshot from `US_WAS_1997_2019.shp.zip`
into a new PostGIS table `walkable_accessibility_score`.

**Do exactly these steps, in order. Do not modify source files.**

### 1. Pull the latest code

```bash
git pull
```

### 2. Verify the shapefile zip and dependencies

Confirm `US_WAS_1997_2019.shp.zip` exists at the repo root (~48 MB):

```bash
ls -lh US_WAS_1997_2019.shp.zip
```

If it's missing, stop and tell me — I'll re-upload it.

Install/refresh Python dependencies. The loader needs `geopandas`,
`psycopg2-binary`, `tqdm`, `sqlalchemy`, and `python-dotenv`, all pinned in
`requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Confirm DB credentials are present

The script reuses `services/db.py`, which reads either `DATABASE_URL` or the
five `PG*` vars (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`).
These should already be set in Replit Secrets. Verify without printing
secrets:

```bash
python -c "import os; [print(f'{k}: {\"set\" if os.environ.get(k) else \"MISSING\"}') for k in ['DATABASE_URL','PGHOST','PGPORT','PGDATABASE','PGUSER','PGPASSWORD']]"
```

At least one of (a) `DATABASE_URL` or (b) the full `PG*` set must be
present. If both are missing, stop and tell me — I'll add them to Secrets.

### 4. Run a read-only inspection first (no writes)

This reports shapefile schema and a naive join-rate probe against the
existing `national_walkability_index` table. It does NOT write to the DB.

```bash
python scripts/inspect_was_shapefile.py
```

Expected output: 215,831 rows, CRS `ESRI:102003`, GEOID column `ID`, WAS
column `WAS2019`, and a join-rate percentage between NWI `geoid20` and
WAS `ID`. Report that percentage back to me (it should be somewhere
between ~80% and ~95%).

### 5. Run the loader with auto-confirm

The script normally prompts `[y/N]`. Since you're running non-interactively,
pass `--yes`:

```bash
python scripts/load_walkable_accessibility_score.py --yes
```

This will:

- Drop `walkable_accessibility_score` if it exists
- Create the table (`geoid VARCHAR(12) PK`, `was_2019 NUMERIC(5,2)`,
  `geometry GEOMETRY(Geometry, 4326)`)
- Reproject from `ESRI:102003` to `EPSG:4326`
- Insert ~215,831 rows in 1,000-row chunks with a `tqdm` progress bar
- Create the `was_geom_idx` GiST spatial index
- Run `ANALYZE walkable_accessibility_score`

Expected runtime: ~2-5 minutes depending on the Repl's connection to the
DB. If it crashes partway through, the `DROP TABLE IF EXISTS` at the top
makes re-runs safe — just run it again.

### 6. Validate the schema

```bash
python scripts/validate_schema.py
```

Expected output includes both:

```
OK: national_walkability_index schema valid
OK: walkable_accessibility_score schema valid
```

If you see `WARNING: Table 'walkable_accessibility_score' does not exist`,
the loader didn't commit — re-run step 5 and tell me the full output.

### 7. Spot-check via SQL

Run these in the DB and paste the results back to me:

```sql
-- Count rows and null rate for was_2019
SELECT COUNT(*) AS total,
       COUNT(was_2019) AS with_was,
       ROUND(100.0 * COUNT(was_2019) / COUNT(*), 2) AS pct_with_was
FROM walkable_accessibility_score;

-- Naive join coverage with NWI
SELECT COUNT(*) AS nwi_total,
       COUNT(was.was_2019) AS nwi_with_was,
       ROUND(100.0 * COUNT(was.was_2019) / COUNT(*), 2) AS pct_joined
FROM national_walkability_index nwi
LEFT JOIN walkable_accessibility_score was ON was.geoid = nwi.geoid20;

-- Sample 5 rows
SELECT geoid, was_2019 FROM walkable_accessibility_score LIMIT 5;
```

### 8. Smoke-test the API

Start the API (or restart it if it's already running in this Repl) and hit
`/nwi/summary/by-query` with a known address. Confirm the response now
includes top-level `was`, `amenity_richness`, and `hollow_neighborhood`
blocks, and that each item in `block_groups` has a `was_2019` field. Paste
the relevant response snippet back to me.

### 9. Do NOT do

- Do not modify `services/`, `api/`, `tests/`, or `scripts/` source files.
- Do not commit anything. The code is already committed locally; your job
  is ingest + validation only.
- Do not delete `US_WAS_1997_2019.shp.zip` — we may want it around for
  re-runs.

---

## When done

Reply with:

1. Inspection join-rate percentage (step 4)
2. Loader's final row count and elapsed time (step 5)
3. The three SQL query results (step 7)
4. The API response snippet (step 8)

If anything fails, paste the full error message and stop rather than
trying to fix it yourself.
