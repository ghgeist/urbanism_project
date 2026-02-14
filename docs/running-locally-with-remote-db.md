# Running Locally with the Database on Replit

You can run the Streamlit app, FastAPI backend, and React frontend on your machine while the PostgreSQL database lives on Replit (or any remote host).

## 1. Get database credentials from Replit

In your Replit project:

1. Open **Secrets** (lock icon in the sidebar).
2. Copy the PostgreSQL variables. Replit may expose:
   - **Option A:** Individual vars: `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`
   - **Option B:** A single **connection URL** (e.g. `postgresql://user:password@host:port/database` or `postgres://...`)

If you use a **Neon** or **Supabase** (or other) database that Replit is pointed at, use that same URL or the same PG* values—they are reachable from your laptop.

**Important:** Replit’s **built-in** PostgreSQL is often only reachable from inside the Replit environment. If you only have Replit’s internal Postgres:

- You **cannot** connect to it directly from your local machine.
- Options: **(1)** Run the app on Replit (don’t run locally), or **(2)** Create a cloud Postgres (e.g. [Neon](https://neon.tech), [Supabase](https://supabase.com)) that both Replit and your laptop can use, load the walkability data there once, then point local and Replit at that same database.

## 2. Configure your local environment

In the repo root, create a `.env` file (it’s gitignored). Use **either** PG* vars **or** a single URL.

### Option A: Individual PG* variables

```env
PGHOST=your-db-host.example.com
PGPORT=5432
PGDATABASE=your_database
PGUSER=your_user
PGPASSWORD=your_password
```

Replace with the values from Replit Secrets (or your Neon/Supabase dashboard).

### Option B: Single connection URL

```env
DATABASE_URL=postgresql://user:password@host:port/database
```

Use the exact URL Replit or your provider gives you. If the URL uses `postgres://`, the app accepts it (psycopg2 handles both). For Neon, add `?sslmode=require` if required:

```env
DATABASE_URL=postgresql://user:password@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require
```

## 3. Load environment variables when you run commands

The app reads **environment variables**, not the `.env` file by itself. Use one of these:

**PowerShell (Windows):**

```powershell
Get-Content .env | ForEach-Object { if ($_ -match '^([^#][^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process') } }
uvicorn api.main:app --reload
streamlit run app.py
```

**Manual (any OS):** Export or set each var in your shell, then run the app.

**Or use a helper:** Many setups use `python-dotenv`. If you add it, you can load `.env` in code (e.g. in `app.py` or a small `scripts/run_local.py` that loads dotenv then starts the app). The repo does not depend on dotenv today; you can add it for local convenience.

## 4. Run the stack locally

1. **Backend (FastAPI)** — from repo root:
   ```bash
   uvicorn api.main:app --reload
   ```
   Default: http://127.0.0.1:8000

2. **Streamlit app** — from repo root:
   ```bash
   streamlit run app.py
   ```

3. **React frontend** (optional) — from `frontend/`:
   ```bash
   npm run dev
   ```
   Default: http://localhost:5173. It talks to the FastAPI backend (set `VITE_API_URL` if the API is not at http://127.0.0.1:8000).

## 5. Verify the connection

From repo root:

```bash
python scripts/check_config.py
```

If PG* or DATABASE_URL are set correctly, the script reports success. Then try a request to the API or open the Streamlit app and run a search.

## Troubleshooting

| Issue | What to try |
|--------|-------------|
| “Missing required database environment variables” | Set either all of `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` or a single `DATABASE_URL`. |
| “Connection refused” / “could not connect” | The DB host must be reachable from your machine. Replit’s built-in Postgres often is not; use a cloud Postgres (Neon, Supabase, etc.) that allows external connections. |
| SSL errors with Neon | Add `?sslmode=require` to `DATABASE_URL`. |
| Streamlit doesn’t see env vars | Ensure variables are set in the same shell session that runs `streamlit run app.py`, or use a `.env` loader (e.g. python-dotenv) if you add one. |
