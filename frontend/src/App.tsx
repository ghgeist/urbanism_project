import { lazy, useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppLayout } from "./layouts/AppLayout";
import { Explore } from "./pages/Explore";
import "./App.css";
import "./mobile.css";

const Compare = lazy(() => import("./pages/Compare").then((module) => ({ default: module.Compare })));
const Dashboard = lazy(() => import("./pages/Dashboard").then((module) => ({ default: module.Dashboard })));
const Method = lazy(() => import("./pages/Method").then((module) => ({ default: module.Method })));

const HEALTH_POLL_INTERVAL_MS = 2000;
const HEALTH_REQUEST_TIMEOUT_MS = 1500;
const MAX_COLD_START_WAIT_MS = 12000;

function isReplitAutoscaleProduction(): boolean {
  if (!import.meta.env.PROD || typeof window === "undefined") {
    return false;
  }

  const hostname = window.location.hostname.toLowerCase();
  return hostname.endsWith(".replit.dev") || hostname.endsWith(".repl.co");
}

function App() {
  const [readyToRenderApp, setReadyToRenderApp] = useState(() => !isReplitAutoscaleProduction());

  useEffect(() => {
    if (!isReplitAutoscaleProduction()) {
      return;
    }

    let isActive = true;
    const timerIds: { pollIntervalId?: number; maxWaitTimeoutId?: number } = {};

    const clearGateTimers = () => {
      if (timerIds.pollIntervalId !== undefined) {
        window.clearInterval(timerIds.pollIntervalId);
      }
      if (timerIds.maxWaitTimeoutId !== undefined) {
        window.clearTimeout(timerIds.maxWaitTimeoutId);
      }
    };

    const openGate = () => {
      if (!isActive) return;
      clearGateTimers();
      setReadyToRenderApp(true);
    };

    const checkHealth = async () => {
      const controller = new AbortController();
      const requestTimeoutId = window.setTimeout(() => controller.abort(), HEALTH_REQUEST_TIMEOUT_MS);

      try {
        const response = await fetch("/health", { signal: controller.signal });
        if (response.ok) {
          openGate();
        }
      } catch {
        // Keep polling until healthy or max wait is reached.
      } finally {
        window.clearTimeout(requestTimeoutId);
      }
    };

    void checkHealth();
    timerIds.pollIntervalId = window.setInterval(() => {
      void checkHealth();
    }, HEALTH_POLL_INTERVAL_MS);
    timerIds.maxWaitTimeoutId = window.setTimeout(() => {
      openGate();
    }, MAX_COLD_START_WAIT_MS);

    return () => {
      isActive = false;
      clearGateTimers();
    };
  }, []);

  if (!readyToRenderApp) {
    return (
      <main className="startup-gate" role="status" aria-live="polite">
        <h1>Starting demo...</h1>
        <p>This deployment may take a few extra seconds on first launch.</p>
      </main>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Explore />} />
          <Route path="compare" element={<Compare />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="method" element={<Method />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
