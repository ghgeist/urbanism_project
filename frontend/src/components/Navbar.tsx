/**
 * Minimal top navigation: product name, Explore / Compare / Method.
 * Civic, neutral tone; active route highlighted subtly.
 */

import { NavLink } from "react-router-dom";

const navLinks = [
  { to: "/", label: "Explore", end: true },
  { to: "/compare", label: "Compare", end: false },
  { to: "/method", label: "Method", end: false },
] as const;

export function Navbar() {
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
    </nav>
  );
}
