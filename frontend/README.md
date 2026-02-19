# Frontend – Slack Surface Explorer

React + TypeScript + Vite app for the walkability Explore (and future Compare) experience. Consumes the FastAPI backend (`/health`, `/geocode`, `/nwi/summary`, `/nwi/summary/by-query`).

## Run locally

**One command (recommended)** – from repo root, start both backend and frontend:

```bash
./scripts/run_dev.sh
```

Or with bash: `bash scripts/run_dev.sh`. Backend runs on port 8000, frontend on port 5000 (see `vite.config.ts`). Ctrl+C stops both.

**Manual (two terminals):**

1. Start the API from repo root: `uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload` (requires PG* env and PostGIS).
2. From `frontend/`: `npm install` then `npm run dev`.
3. Open the dev server URL (see terminal; e.g. http://localhost:5000). When `VITE_API_URL` is unset, the app uses the same origin so Vite proxies `/health`, `/geocode`, and `/nwi` to the backend—no CORS. Override with `VITE_API_URL` if needed (see `.env.example`).

### Running from SSH / external terminal (e.g. Cursor)

If you connect to this Replit via SSH and `node`/`npm` are not on your PATH,
start a **new** shell session (close and reconnect). The `~/.bash_profile`
automatically loads the Replit environment, including Node.js, on login.

After reconnecting you can run:

```bash
cd frontend && npm install && npm run dev
```

If that still doesn't work, you can manually load the environment in your
current session:

```bash
source /run/replit/env/latest
```

## Scripts

- `npm run dev` – dev server (Vite)
- `npm run build` – production build
- `npm run preview` – preview production build
- `npm run test` / `npm run test:run` – Vitest unit tests
- `npm run e2e` / `npm run e2e:run` – Playwright E2E (starts dev server unless one is already running). First time: `npx playwright install chromium`
- `npm run lint` – ESLint

## Testing

> **📖 For comprehensive testing documentation covering both backend and frontend, see [`docs/TESTING.md`](../docs/TESTING.md)**

### Quick Start

```bash
# Unit tests (watch mode)
npm run test

# Unit tests (single run)
npm run test:run

# E2E tests (headless)
npm run e2e:run
```

### Test Structure

- **Unit Tests**: `src/**/*.test.ts` and `src/**/*.test.tsx` (Vitest + React Testing Library)
- **E2E Tests**: `e2e/**/*.spec.ts` (Playwright)

### Test Coverage

- **Components**: `MapView`, `SummaryCards`, `CompareTable` (rendering, props, events)
- **API Client**: Request/response handling, error mapping
- **URL Parameters**: `exploreParams`, `compareParams`, `radiusParams` (parsing, validation)
- **Hooks**: `useUrlDrivenSearch` (state management, URL sync)

### Adding Tests

When adding new functionality:

1. Create test file: `ComponentName.test.tsx` or `utility.test.ts`
2. Use React Testing Library: `render`, `screen`, `userEvent`
3. Mock external dependencies: Leaflet, fetch, React Router
4. Test user-facing behavior, not implementation details

See `src/components/MapView.test.tsx` for examples.
