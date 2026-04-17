/**
 * Top navigation: hamburger (left), brand (center), and a slide-in drawer
 * on phones with scrim, body-scroll lock, focus management, and
 * Escape-to-close.
 *
 * Information architecture on phones:
 *   - Primary destinations (Explore / Compare / Dashboard) live in the
 *     bottom tab bar (see MobileTabBar).
 *   - This drawer holds *secondary* and *utility* items: the Method
 *     reference page, external links (GitHub, Substack, personal site),
 *     and data attribution.
 * On tablet/desktop the inline link list is shown instead.
 */

import { useEffect, useRef, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";

/** Inline (desktop) primary nav. */
const navLinks = [
  { to: "/", label: "Explore", end: true },
  { to: "/compare", label: "Compare", end: false },
  { to: "/dashboard", label: "Dashboard", end: false },
  { to: "/method", label: "Method", end: false },
] as const;

/** Drawer = secondary + utility links only (NOT the primary tab routes). */
const drawerSecondary = [
  { to: "/method", label: "Method & methodology", end: false },
] as const;

const drawerExternal = [
  { href: "https://github.com/ghgeist", label: "GitHub" },
  { href: "https://thedonkeyaxiom.substack.com/", label: "Substack" },
  { href: "https://granthgeist.com", label: "Author site" },
] as const;

export function Navbar() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const location = useLocation();
  const toggleRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);
  const previouslyFocusedRef = useRef<HTMLElement | null>(null);

  // Close on route change.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Route transitions should always collapse the mobile drawer immediately.
    setDrawerOpen(false);
  }, [location.pathname]);

  // Manage the `inert` attribute imperatively. React's prop normalization
  // around boolean attributes is inconsistent across versions, so we set
  // and remove the attribute directly to guarantee descendants are removed
  // from the tab order / hit testing / a11y tree when the drawer is closed.
  useEffect(() => {
    const el = drawerRef.current;
    if (!el) return;
    if (drawerOpen) {
      el.removeAttribute("inert");
    } else {
      el.setAttribute("inert", "");
    }
  }, [drawerOpen]);

  // Body scroll lock + focus management while drawer is open.
  useEffect(() => {
    if (typeof document === "undefined") return;
    if (!drawerOpen) return;

    const previousOverflow = document.body.style.overflow;
    const toggleEl = toggleRef.current;
    document.body.style.overflow = "hidden";
    previouslyFocusedRef.current = document.activeElement as HTMLElement | null;

    // Focus the first interactive element in the drawer once mounted.
    const focusTimer = window.setTimeout(() => {
      const firstLink = drawerRef.current?.querySelector<HTMLElement>("a, button");
      firstLink?.focus();
    }, 30);

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setDrawerOpen(false);
        return;
      }
      if (e.key !== "Tab") return;
      // Simple focus trap: keep focus inside the drawer.
      const focusables = drawerRef.current?.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled])'
      );
      if (!focusables || focusables.length === 0) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (e.shiftKey && active === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && active === last) {
        e.preventDefault();
        first.focus();
      }
    }

    window.addEventListener("keydown", onKeyDown);

    return () => {
      window.clearTimeout(focusTimer);
      window.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
      // Return focus to the toggle (or whatever was focused before opening).
      const fallback = previouslyFocusedRef.current ?? toggleEl;
      fallback?.focus?.();
    };
  }, [drawerOpen]);

  return (
    <nav className="app-nav" role="navigation" aria-label="Main">
      <div className="app-nav__inner">
        <button
          ref={toggleRef}
          type="button"
          className="app-nav__toggle"
          aria-label={drawerOpen ? "Close menu" : "Open menu"}
          aria-expanded={drawerOpen}
          aria-controls="primary-nav-drawer"
          onClick={() => setDrawerOpen((v) => !v)}
        >
          <span className="app-nav__toggle-bar" aria-hidden />
          <span className="app-nav__toggle-bar" aria-hidden />
          <span className="app-nav__toggle-bar" aria-hidden />
        </button>

        <NavLink to="/" className="app-nav__brand" end>
          <span className="app-nav__brand-icon" aria-hidden>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="28" height="28" fill="currentColor">
              <title>City</title>
              <path d="M0 32h4V18H0v14zm6 0h4V12h-4v20zm8 0h4V8h-4v24zm6 0h4V14h-4v18zm8 0h4V6h-4v26zm6 0h4V10h-4v22zm6 0h6V14h-6v18z" />
            </svg>
          </span>
          Walkability Explorer
        </NavLink>

        {/* Inline link list for tablet/desktop — hidden on phones via CSS. */}
        <ul className="app-nav__links">
          {navLinks.map(({ to, label, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                className={({ isActive }) =>
                  `app-nav__link ${isActive ? "app-nav__link--active" : ""}`
                }
              >
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>

      {/* Mobile drawer + scrim. Mounted always so transitions work; visibility
          and pointer events are gated by the --open modifier. */}
      <div
        className={`app-nav__scrim ${drawerOpen ? "app-nav__scrim--open" : ""}`}
        onClick={() => setDrawerOpen(false)}
        aria-hidden={!drawerOpen}
      />
      <aside
        id="primary-nav-drawer"
        ref={drawerRef}
        className={`app-nav__drawer ${drawerOpen ? "app-nav__drawer--open" : ""}`}
        role="dialog"
        aria-modal={drawerOpen}
        aria-label="Main menu"
        aria-hidden={!drawerOpen}
      >
        <div className="app-nav__drawer-header">
          <span className="app-nav__drawer-title">Menu</span>
          <button
            type="button"
            className="app-nav__drawer-close"
            aria-label="Close menu"
            onClick={() => setDrawerOpen(false)}
            tabIndex={drawerOpen ? 0 : -1}
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M6 6l12 12" />
              <path d="M18 6 6 18" />
            </svg>
          </button>
        </div>
        <ul className="app-nav__drawer-links">
          {drawerSecondary.map(({ to, label, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                className={({ isActive }) =>
                  `app-nav__drawer-link ${isActive ? "app-nav__drawer-link--active" : ""}`
                }
                tabIndex={drawerOpen ? 0 : -1}
              >
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
        <div className="app-nav__drawer-section" aria-label="External links">
          <span className="app-nav__drawer-section-label">More</span>
          <ul className="app-nav__drawer-links">
            {drawerExternal.map(({ href, label }) => (
              <li key={href}>
                <a
                  href={href}
                  className="app-nav__drawer-link"
                  target="_blank"
                  rel="noopener noreferrer"
                  tabIndex={drawerOpen ? 0 : -1}
                >
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </div>
        <p className="app-nav__drawer-attribution">
          Data: EPA National Walkability Index · © Grant Geist
        </p>
      </aside>
    </nav>
  );
}
