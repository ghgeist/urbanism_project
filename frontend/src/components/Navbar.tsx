/**
 * Top navigation: brand + links. On narrow screens the links collapse
 * behind a hamburger toggle, then expand into a stacked menu.
 */

import { useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";

const navLinks = [
  { to: "/", label: "Explore", end: true },
  { to: "/compare", label: "Compare", end: false },
  { to: "/dashboard", label: "Dashboard", end: false },
  { to: "/method", label: "Method", end: false },
] as const;

export function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  // Close the mobile menu whenever the user navigates.
  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  return (
    <nav className="app-nav" role="navigation" aria-label="Main">
      <div className="app-nav__inner">
        <NavLink to="/" className="app-nav__brand" end>
          <span className="app-nav__brand-icon" aria-hidden>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="28" height="28" fill="currentColor">
              <title>City</title>
              <path d="M0 32h4V18H0v14zm6 0h4V12h-4v20zm8 0h4V8h-4v24zm6 0h4V14h-4v18zm8 0h4V6h-4v26zm6 0h4V10h-4v22zm6 0h6V14h-6v18z" />
            </svg>
          </span>
          Walkability Explorer
        </NavLink>

        <button
          type="button"
          className="app-nav__toggle"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
          aria-controls="primary-nav-links"
          onClick={() => setMenuOpen((v) => !v)}
        >
          <span className="app-nav__toggle-bar" aria-hidden />
          <span className="app-nav__toggle-bar" aria-hidden />
          <span className="app-nav__toggle-bar" aria-hidden />
        </button>

        <ul
          id="primary-nav-links"
          className={`app-nav__links ${menuOpen ? "app-nav__links--open" : ""}`}
        >
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
    </nav>
  );
}
