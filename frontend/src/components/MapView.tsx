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

  useEffect(() => {
    if (!containerRef.current) return;

    if (mapRef.current) {
      mapRef.current.setView([lat, lon], mapRef.current.getZoom());
      const marker = markerRef.current;
      if (marker) {
        marker.setLatLng([lat, lon]);
        const tooltip = marker.getTooltip();
        if (tooltip) tooltip.setContent(label ?? "");
        else if (label) marker.bindTooltip(label, { permanent: false });
      }
      return;
    }

    const map = L.map(containerRef.current).setView([lat, lon], 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    const marker = L.marker([lat, lon]);
    marker.addTo(map);
    if (label) marker.bindTooltip(label, { permanent: false });
    markerRef.current = marker;

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
  }, [lat, lon, label]);

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
