# Mobile audit — Walkability Explorer

Date: 2026-04-17 (Task #4 polish & verification).

## Audit method

Lighthouse CLI is not installable in this Replit environment (Chromium download is large and `npx` is gated). Instead, the mobile experience is verified through:

- A Pixel 5 Playwright project (`mobile`) running `e2e/mobile.spec.ts` (5 specs covering hamburger nav, fullscreen map + ESC, Explore form layout, Compare form layout, Compare table-as-cards reflow with mocked API).
- Manual visual review at desktop and mobile widths.

To regenerate a real Lighthouse report locally, install Chrome and run:

```bash
npx lighthouse http://localhost:5000 \
  --preset=desktop \
  --output=html \
  --output-path=frontend/lighthouse/desktop.html
npx lighthouse http://localhost:5000 \
  --emulated-form-factor=mobile \
  --output=html \
  --output-path=frontend/lighthouse/mobile.html
```

## Manifest / installability

- `manifest.webmanifest` references four icons:
  - `icon-192.png` (192×192, `purpose: "any"`)
  - `icon-512.png` (512×512, `purpose: "any"`)
  - `icon-maskable-512.png` (512×512, `purpose: "maskable"`, ≥60% safe zone)
  - `favicon.svg` (`purpose: "any"`)
- `display: standalone`, `theme_color: #1e40af`, `background_color: #f5f5f5`.
- Viewport meta is set in `index.html` with `width=device-width, initial-scale=1`.

This satisfies the basic PWA installability criteria (HTTPS in production + service worker would complete the picture; SW is intentionally out of scope).

## Mobile-specific verifications (covered by `e2e/mobile.spec.ts`)

| Behavior | Test |
| --- | --- |
| Nav links collapse behind hamburger; toggle has correct `aria-expanded` | `Mobile navigation` |
| Tapping a menu item navigates and auto-closes the menu | `Mobile navigation` |
| Explore form input + submit stack to ≥70% width and meet 44px touch target | `Mobile Explore form` |
| Map "Expand" enters fullscreen and ESC exits | `Mobile map fullscreen` |
| Compare form stacks; submit ≥70% width and 44px tall | `Mobile Compare layout` |
| Compare table reflows to stacked cards with `data-label` headers per cell | `Mobile Compare layout (mocked)` |

## Known limitations

- No real Lighthouse score in this env. CI should add Chromium + Lighthouse for an authoritative number.
- No service worker / offline cache. Out of scope for Task #4.
- Mobile testing covers Pixel 5 only; iPhone-specific quirks (notch padding, Safari 100vh) rely on `env(safe-area-inset-*)` which is not asserted.
