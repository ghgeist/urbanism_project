/**
 * Leaflet map centered on origin; no geometry tiles yet (evidence layer in Phase 1).
 */

import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix default marker icon with Vite/bundlers (images path is not available).
const DefaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

interface MapViewProps {
  lat: number;
  lon: number;
  radiusMiles: number;
  label?: string | null;
  /** When true, container height is controlled by parent (e.g. split layout). */
  fillHeight?: boolean;
}

export function MapView({ lat, lon, radiusMiles, label, fillHeight }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);

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

  // Teardown map on unmount so the Leaflet instance and listeners are always removed.
  // (The effect above does not return a cleanup when it creates or updates the map.)
  useEffect(() => {
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        markerRef.current = null;
      }
    };
  }, []);

  return (
    <div className="map-view">
      <div
        ref={containerRef}
        className="map-view__container"
        style={fillHeight ? undefined : { height: "360px" }}
      />
      <p className="map-view__caption">
        Center: {lat.toFixed(4)}, {lon.toFixed(4)} · Radius: {radiusMiles} mi
      </p>
    </div>
  );
}
