/**
 * App shell: Navbar, main content (Outlet), Footer, and mobile bottom tab bar.
 * Main has consistent max-width and padding; pages render inside.
 */

import { Outlet } from "react-router-dom";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";
import { MobileTabBar } from "../components/MobileTabBar";

export function AppLayout() {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="app-main">
        <Outlet />
      </main>
      <Footer />
      <MobileTabBar />
    </div>
  );
}
