/**
 * Minimal top navigation: product name, Explore / Compare / Method, optional GitHub.
 * Civic, neutral tone; active route highlighted subtly.
 */

import { NavLink } from "react-router-dom";

const GITHUB_URL = import.meta.env.VITE_GITHUB_URL as string | undefined;

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
        {GITHUB_URL ? (
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="app-nav__github"
          >
            GitHub
          </a>
        ) : null}
      </div>
    </nav>
  );
}
