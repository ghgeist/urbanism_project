/**
 * Leaflet map centered on origin with a choropleth layer of block groups
 * colored by walkability relative to the area mean NWI.
 */

import { useEffect, useRef } from "react";
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
}

export function MapView({ lat, lon, radiusMiles, label, blockGroups, nwiMean, fillHeight }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);
  const blockGroupsLayerRef = useRef<L.GeoJSON | null>(null);

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
      mapRef.current.setView([lat, lon], mapRef.current.getZoom());
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

    const map = L.map(container).setView([lat, lon], 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    const marker = L.marker([lat, lon]);
    marker.addTo(map);
    if (label) marker.bindTooltip(label, { permanent: false });
    markerRef.current = marker;
    mapRef.current = map;
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
        const delta = nwi != null && nwiMean != null ? nwi - nwiMean : 0;
        return {
          fillColor: nwiDeltaColor(delta),
          fillOpacity: 0.45,
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
    <div className="map-view">
      <div
        ref={containerRef}
        className="map-view__container"
        style={fillHeight ? undefined : { height: "360px" }}
      />
      {showLegend && (
        <div className="map-view__legend">
          {NWI_TIERS.map((tier) => (
            <span key={tier.color} className="map-view__legend-item">
              <span className="map-view__legend-swatch" style={{ background: tier.color }} />
              {tier.label}
            </span>
          ))}
        </div>
      )}
      <p className="map-view__caption">
        Center: {lat.toFixed(4)}, {lon.toFixed(4)} · Radius: {radiusMiles} mi
      </p>
    </div>
  );
}
