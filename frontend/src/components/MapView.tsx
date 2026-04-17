/**
 * Leaflet map centered on origin with a choropleth layer of block groups
 * colored by walkability relative to the area mean NWI.
 */

import { useEffect, useRef, useState, type ReactNode } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { BlockGroupFeature } from "../types/api";

// Fix default marker icon with Vite/bundlers (images path is not available).
const DefaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

// NWI delta thresholds for the five-tier color scale.
// NWI ranges 1–20. ±1 point captures the zone of statistical noise around
// the local mean; ±3 points marks a tier of practical significance (roughly
// one population std-dev in typical US metro census block groups).
const NWI_TIER_HIGH = 3;
const NWI_TIER_LOW  = 1;

// Fill color for block groups where natwalkind or the area mean is unavailable.
// Must be visually distinct from every NWI_TIERS color so users are never
// misled into thinking an unknown block group is "Near avg".
const NWI_NO_DATA_COLOR = "#9ca3af";  // neutral gray

// Single source of truth for colors and labels. nwiDeltaColor and the legend
// both iterate this array so they can never fall out of sync.
const NWI_TIERS: Array<{ min: number; color: string; label: string }> = [
  { min:  NWI_TIER_HIGH,  color: "#1a7d3e", label: `Well above avg (≥+${NWI_TIER_HIGH})` },
  { min:  NWI_TIER_LOW,   color: "#5cb85c", label: `Above avg (+${NWI_TIER_LOW} to +${NWI_TIER_HIGH})` },
  { min: -NWI_TIER_LOW,   color: "#f0ad4e", label: `Near avg (±${NWI_TIER_LOW})` },
  { min: -NWI_TIER_HIGH,  color: "#e8622a", label: `Below avg (−${NWI_TIER_LOW} to −${NWI_TIER_HIGH})` },
  { min: -Infinity,        color: "#c0392b", label: `Well below avg (<−${NWI_TIER_HIGH})` },
];

/** Color a block group by its NWI delta relative to the area mean. */
function nwiDeltaColor(delta: number): string {
  return NWI_TIERS.find((t) => delta >= t.min)?.color ?? "#c0392b";
}

interface MapViewProps {
  lat: number;
  lon: number;
  radiusMiles: number;
  label?: string | null;
  blockGroups?: BlockGroupFeature[] | null;
  nwiMean?: number | null;
  /** When true, container height is controlled by parent (e.g. split layout). */
  fillHeight?: boolean;
  /** Fires after a user-driven pan/zoom finishes (not after programmatic setView). */
  onCenterChanged?: (lat: number, lon: number) => void;
  /** Optional overlay rendered inside the map view (e.g. "Search this area" pill). */
  overlay?: ReactNode;
  /** Hide the legend/caption rows (useful inside compact / map-first layouts). */
  hideChrome?: boolean;
}

export function MapView({ lat, lon, radiusMiles, label, blockGroups, nwiMean, fillHeight, onCenterChanged, overlay, hideChrome }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);
  const blockGroupsLayerRef = useRef<L.GeoJSON | null>(null);
  const fullscreenToggleRef = useRef<HTMLButtonElement>(null);
  const previouslyFocusedRef = useRef<HTMLElement | null>(null);
  /** Target center of an in-flight programmatic setView/fitBounds. The next
   *  moveend whose center matches this target is swallowed (so we don't
   *  treat our own setView as a user-driven move). Comparing to the target
   *  is more robust than a single boolean flag — if the user pans before a
   *  pending programmatic moveend has fired, the centers won't match and
   *  the user pan still emits. */
  const programmaticTargetRef = useRef<{ lat: number; lng: number } | null>(null);
  const onCenterChangedRef = useRef(onCenterChanged);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    onCenterChangedRef.current = onCenterChanged;
  }, [onCenterChanged]);

  // Lock body scroll while the map is in fullscreen mode and ensure Leaflet
  // recalculates its size when the container dimensions change.
  useEffect(() => {
    if (typeof document === "undefined") return;
    const previousOverflow = document.body.style.overflow;
    if (isFullscreen) {
      document.body.style.overflow = "hidden";
      previouslyFocusedRef.current = document.activeElement as HTMLElement | null;
      // Move focus to the close button so keyboard users don't get trapped
      // tabbing into the now-obscured background content.
      window.setTimeout(() => fullscreenToggleRef.current?.focus(), 60);
    }
    // Defer invalidateSize so the new layout has been applied.
    const id = window.setTimeout(() => {
      mapRef.current?.invalidateSize();
    }, 50);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.clearTimeout(id);
      // Return focus to the originally-focused element when leaving fullscreen.
      if (!isFullscreen) {
        previouslyFocusedRef.current?.focus?.();
      }
    };
  }, [isFullscreen]);

  // Allow ESC to exit fullscreen.
  useEffect(() => {
    if (!isFullscreen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsFullscreen(false);
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [isFullscreen]);

  // Create or update map when lat/lon/label change.
  useEffect(() => {
    if (!containerRef.current) return;

    const existingMap = mapRef.current;
    const container = containerRef.current;

    // If we have a map but it's no longer in our container (e.g. DOM node was replaced by React),
    // remove the orphan so we don't leak and create a fresh map in the current container.
    if (existingMap && existingMap.getContainer() !== container) {
      existingMap.remove();
      mapRef.current = null;
      markerRef.current = null;
      blockGroupsLayerRef.current = null;
    }

    if (mapRef.current) {
      // Only call setView if the coords actually changed — avoids spurious
      // programmatic-target tracking on no-op updates.
      const currentCenter = mapRef.current.getCenter();
      const COORD_EPS = 1e-6;
      if (Math.abs(currentCenter.lat - lat) > COORD_EPS || Math.abs(currentCenter.lng - lon) > COORD_EPS) {
        programmaticTargetRef.current = { lat, lng: lon };
        mapRef.current.setView([lat, lon], mapRef.current.getZoom());
      }
      const marker = markerRef.current;
      if (marker) {
        marker.setLatLng([lat, lon]);
        const tooltip = marker.getTooltip();
        if (label != null && label !== "") {
          if (tooltip) tooltip.setContent(label);
          else marker.bindTooltip(label, { permanent: false });
        } else if (tooltip) {
          marker.unbindTooltip();
        }
      }
      return;
    }

    programmaticTargetRef.current = { lat, lng: lon };
    const map = L.map(container);
    map.setView([lat, lon], 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    const marker = L.marker([lat, lon]);
    marker.addTo(map);
    if (label) marker.bindTooltip(label, { permanent: false });
    markerRef.current = marker;
    mapRef.current = map;

    // Expose the Leaflet map in dev so E2E tests can pan/zoom the map
    // programmatically (synthetic mouse events from Playwright don't drive
    // Leaflet's drag handler on touch device profiles like Pixel 5).
    if (import.meta.env.DEV && typeof window !== "undefined") {
      (window as unknown as { __leafletMap?: L.Map }).__leafletMap = map;
    }

    // Emit user-driven moves only.
    map.on("moveend", () => {
      const c = map.getCenter();
      const target = programmaticTargetRef.current;
      // Swallow the moveend that completes a pending programmatic setView,
      // identified by the center landing on the target (within ~1m).
      if (target && Math.abs(c.lat - target.lat) < 1e-5 && Math.abs(c.lng - target.lng) < 1e-5) {
        programmaticTargetRef.current = null;
        return;
      }
      onCenterChangedRef.current?.(c.lat, c.lng);
    });
    // No cleanup here: reuse map on prop changes (update path above). Unmount cleanup is in the effect below.
  }, [lat, lon, label]);

  // Add or replace the block group choropleth layer when data changes.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Remove existing choropleth layer.
    if (blockGroupsLayerRef.current) {
      blockGroupsLayerRef.current.remove();
      blockGroupsLayerRef.current = null;
    }
    if (!blockGroups || blockGroups.length === 0) return;

    const geojsonData = {
      type: "FeatureCollection" as const,
      features: blockGroups.map((bg) => ({
        type: "Feature" as const,
        properties: { geoid20: bg.geoid20, natwalkind: bg.natwalkind },
        geometry: bg.geometry,
      })),
    };

    const layer = L.geoJSON(geojsonData, {
      style: (feature) => {
        const nwi = (feature?.properties?.natwalkind as number | null) ?? null;
        const hasData = nwi != null && nwiMean != null;
        return {
          fillColor: hasData ? nwiDeltaColor(nwi - nwiMean) : NWI_NO_DATA_COLOR,
          fillOpacity: hasData ? 0.45 : 0.3,  // lower opacity flags missing data
          color: "#444",
          weight: 0.8,
        };
      },
    });

    layer.addTo(map);
    layer.bringToBack();  // Z-order: tiles (bottom) → choropleth → marker (top).
    blockGroupsLayerRef.current = layer;
  }, [blockGroups, nwiMean]);

  // Teardown map on unmount so the Leaflet instance and listeners are always removed.
  useEffect(() => {
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        markerRef.current = null;
        blockGroupsLayerRef.current = null;
      }
    };
  }, []);

  const showLegend = blockGroups && blockGroups.length > 0;

  return (
    <div className={`map-view ${isFullscreen ? "map-view--fullscreen" : ""}`}>
      <button
        ref={fullscreenToggleRef}
        type="button"
        className="map-view__fullscreen-toggle"
        onClick={() => setIsFullscreen((v) => !v)}
        aria-label={isFullscreen ? "Exit fullscreen map" : "Expand map to fullscreen"}
        aria-pressed={isFullscreen}
      >
        {isFullscreen ? "Close map" : "Expand map"}
      </button>
      <div
        ref={containerRef}
        className="map-view__container"
        style={fillHeight || isFullscreen ? undefined : { height: "360px" }}
      />
      {overlay && <div className="map-view__overlay">{overlay}</div>}
      {showLegend && !hideChrome && (
        <div className="map-view__legend">
          {NWI_TIERS.map((tier) => (
            <span key={tier.color} className="map-view__legend-item">
              <span className="map-view__legend-swatch" style={{ background: tier.color }} />
              {tier.label}
            </span>
          ))}
          <span className="map-view__legend-item">
            <span className="map-view__legend-swatch" style={{ background: NWI_NO_DATA_COLOR }} />
            No data
          </span>
        </div>
      )}
      {!hideChrome && (
        <p className="map-view__caption">
          Center: {lat.toFixed(4)}, {lon.toFixed(4)} · Radius: {radiusMiles} mi
        </p>
      )}
    </div>
  );
}
