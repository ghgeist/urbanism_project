/**
 * Compact footer: data attribution, disclaimer, links to Method and optional GitHub.
 */

import { Link } from "react-router-dom";

const GITHUB_URL = import.meta.env.VITE_GITHUB_URL as string | undefined;
const currentYear = new Date().getFullYear();

export function Footer() {
  return (
    <footer className="app-footer" role="contentinfo">
      <div className="app-footer__inner">
        <span className="app-footer__data">Data: EPA National Walkability Index</span>
        <span className="app-footer__disclaimer">Not causal; descriptive only.</span>
        <span className="app-footer__links">
          <Link to="/method">Method</Link>
          {GITHUB_URL ? (
            <>
              <span className="app-footer__sep" aria-hidden="true">
                ·
              </span>
              <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
                GitHub
              </a>
            </>
          ) : null}
          <span className="app-footer__sep" aria-hidden="true">
            ·
          </span>
          <span className="app-footer__copy">© {currentYear}</span>
        </span>
      </div>
    </footer>
  );
}
