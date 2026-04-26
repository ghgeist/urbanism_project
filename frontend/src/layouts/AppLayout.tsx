/**
 * App shell: Navbar, main content (Outlet), Footer, and mobile bottom tab bar.
 * Main has consistent max-width and padding; pages render inside.
 */

import { Suspense } from "react";
import { Outlet } from "react-router-dom";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";
import { MobileTabBar } from "../components/MobileTabBar";

function RouteFallback() {
  return (
    <div className="startup-gate" role="status" aria-live="polite">
      Loading page...
    </div>
  );
}

export function AppLayout() {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="app-main">
        <Suspense fallback={<RouteFallback />}>
          <Outlet />
        </Suspense>
      </main>
      <Footer />
      <MobileTabBar />
    </div>
  );
}
