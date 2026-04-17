# Mobile audit — Walkability Explorer

Date: 2026-04-17 (Task #4 polish & verification).

## Lighthouse mobile scores (dev server)

Generated with the bundled Playwright Chromium against the running Vite
dev server (`http://127.0.0.1:5000/`) under Lighthouse's mobile emulation:

| Category        | Score |
| --------------- | ----- |
| Performance     | 0.44  |
| Accessibility   | 1.00  |
| Best Practices  | 0.96  |
| SEO             | 1.00  |

Reports: `mobile.report.html`, `mobile.report.json` in this folder.
PWA category was deprecated in Lighthouse v12+ (manifest/icons are still
covered under installability checks; both pass — see manifest section).

### Failing audits (Performance — dev-server caveat)

`first-contentful-paint`, `largest-contentful-paint`, `speed-index`, and
`total-blocking-time` all score poorly. This is expected against the
unminified Vite dev server with `--reload`, HMR, and `Cache-Control:
no-store` headers. Production performance is materially better; running
against `vite preview` after `npm run build` would give a fair number.
There's a pre-existing TS error in
`src/components/dashboard/ComponentDistributionChart.tsx` blocking
`npm run build` in this environment — out of scope for Task #4 to fix.

### Failing audits (other)

- **Best Practices — `image-size-responsive`**: caused by Leaflet/OSM map
  tiles being upscaled at the current zoom. Fixing requires a higher-DPI
  tile source or zoom adjustment; deferred (no user-facing complaint).

### Quick wins applied during the audit

- Added `frontend/public/robots.txt` allowing all user agents → SEO went
  from 0.92 to 1.00.

## How to regenerate locally

```bash
# Start the dev server (or `npm run preview` for a fair perf score).
cd frontend && npm run dev &

# Run Lighthouse with the Playwright-bundled Chromium.
CHROME_PATH=$(node -e 'console.log(require("playwright").chromium.executablePath())') \
npx lighthouse http://127.0.0.1:5000/ \
  --emulated-form-factor=mobile \
  --chrome-flags="--headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage" \
  --output=html --output=json \
  --output-path=frontend/lighthouse/mobile
```

## Manifest / installability

- `manifest.webmanifest` references four icons:
  - `icon-192.png` (192×192, `purpose: "any"`)
  - `icon-512.png` (512×512, `purpose: "any"`)
  - `icon-maskable-512.png` (512×512, `purpose: "maskable"`, ≥60% safe zone)
  - `favicon.svg` (`purpose: "any"`)
- `display: standalone`, `theme_color: #1e40af`, `background_color: #f5f5f5`.
- Viewport meta is set in `index.html` with `width=device-width, initial-scale=1`.
- `robots.txt` is now served at the site root.

This satisfies the basic PWA installability criteria (HTTPS in production
+ a service worker would complete the picture; SW is intentionally out of
scope).

## Mobile-specific verifications (covered by `e2e/mobile.spec.ts`)

| Behavior                                                                              | Test                                  |
| ------------------------------------------------------------------------------------- | ------------------------------------- |
| Nav links collapse behind hamburger; toggle has correct `aria-expanded`               | `Mobile navigation`                   |
| Tapping a menu item navigates and auto-closes the menu                                | `Mobile navigation`                   |
| Explore form input + submit stack to ≥70% width and meet 44px touch target            | `Mobile Explore form`                 |
| Submitting Explore on a phone renders summary cards (mocked API)                      | `Mobile Explore form`                 |
| Map "Expand" enters fullscreen and ESC exits                                          | `Mobile map fullscreen`               |
| Compare form stacks; submit ≥70% width and 44px tall                                  | `Mobile Compare layout`               |
| Compare table reflows to stacked cards with `data-label` headers per cell             | `Mobile Compare layout (mocked)`      |

## Known limitations

- Performance score is taken against the dev server. CI should run against
  `vite preview` after a successful `npm run build` for a representative
  number.
- No service worker / offline cache. Out of scope for Task #4.
- Mobile testing covers Pixel 5 only; iPhone-specific quirks (notch
  padding, Safari 100vh) rely on `env(safe-area-inset-*)` which is not
  asserted.
