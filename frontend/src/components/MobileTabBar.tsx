/**
 * Persistent bottom tab bar for phones. Holds the *primary* destinations
 * (Explore, Compare, Dashboard) so the user can hop between them with their
 * thumb. Secondary / utility links (Method, external links, attribution)
 * live in the slide-in left drawer instead. Hidden on tablet/desktop via
 * CSS.
 */

import { NavLink } from "react-router-dom";

const tabs = [
  {
    to: "/",
    label: "Explore",
    end: true,
    icon: (
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </svg>
    ),
  },
  {
    to: "/compare",
    label: "Compare",
    end: false,
    icon: (
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="M3 6h18" />
        <path d="M3 12h18" />
        <path d="M3 18h12" />
      </svg>
    ),
  },
  {
    to: "/dashboard",
    label: "Dashboard",
    end: false,
    icon: (
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <rect x="3" y="3" width="7" height="9" rx="1" />
        <rect x="14" y="3" width="7" height="5" rx="1" />
        <rect x="14" y="12" width="7" height="9" rx="1" />
        <rect x="3" y="16" width="7" height="5" rx="1" />
      </svg>
    ),
  },
] as const;

export function MobileTabBar() {
  return (
    <nav className="mobile-tabbar" role="navigation" aria-label="Primary">
      {tabs.map(({ to, label, end, icon }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            `mobile-tabbar__tab ${isActive ? "mobile-tabbar__tab--active" : ""}`
          }
        >
          <span className="mobile-tabbar__icon" aria-hidden>{icon}</span>
          <span className="mobile-tabbar__label">{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
