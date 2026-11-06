/* OMNIA — Property Map View (Idealista-like flow)
 *
 * Leaflet + OSM. Prezzo sul pin, cluster, sync selezione, callback bounds
 * per «Cerca in questa zona».
 */
import React, { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { clusterMarkers, CLUSTER_MAX_ZOOM } from "../lib/clustering";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const DEFAULT_CENTER = [41.9028, 12.4964];
const DEFAULT_ZOOM = 6;

function formatPriceShort(m) {
  const v = m.operation === "rent" ? m.rent_monthly : m.price;
  if (!v) return "·";
  const n = Number(v);
  if (m.operation === "rent") {
    return n >= 1000
      ? `€${(n / 1000).toFixed(n >= 10000 ? 0 : 1).replace(".0", "")}k/m`
      : `€${n.toLocaleString("it-IT")}/m`;
  }
  if (n >= 1_000_000) return `€${(n / 1_000_000).toFixed(1).replace(".0", "")}M`;
  if (n >= 1000) return `€${Math.round(n / 1000)}k`;
  return `€${n.toLocaleString("it-IT")}`;
}

function formatPriceFull(m) {
  const v = m.operation === "rent" ? m.rent_monthly : m.price;
  if (!v) return "";
  return m.operation === "rent"
    ? `€ ${Number(v).toLocaleString("it-IT")}/mese`
    : `€ ${Number(v).toLocaleString("it-IT")}`;
}

function priceIcon(m, selected) {
  const label = formatPriceShort(m);
  const bg = selected ? "#C19A6B" : "#0B1E3F";
  const border = selected ? "#0B1E3F" : "#C19A6B";
  const html = `<div style="
    background:${bg};color:#fff;border:2px solid ${border};
    border-radius:999px;padding:4px 10px;font:600 11px/1.2 system-ui,sans-serif;
    white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,.28);
    transform:translateY(-2px);
  ">${label}</div>`;
  return L.divIcon({
    html,
    className: "omnia-price-pin",
    iconSize: [1, 1],
    iconAnchor: [40, 14],
  });
}

function clusterIcon(count) {
  const size = count >= 100 ? 46 : count >= 10 ? 40 : 34;
  return L.divIcon({
    html: `<div style="width:${size}px;height:${size}px;border-radius:9999px;background:#0B1E3F;color:#fff;display:flex;align-items:center;justify-content:center;font:600 12px/1 system-ui,sans-serif;border:2px solid #C19A6B;box-shadow:0 2px 6px rgba(0,0,0,.3)">${count}</div>`,
    className: "omnia-cluster-icon",
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

function FitBounds({ markers, enabled }) {
  const map = useMap();
  useEffect(() => {
    if (!enabled || !markers?.length) return;
    const valid = markers.filter((m) => m.lat && m.lng);
    if (!valid.length) return;
    const bounds = L.latLngBounds(valid.map((m) => [m.lat, m.lng]));
    map.fitBounds(bounds, { padding: [48, 48], maxZoom: 14 });
  }, [markers, map, enabled]);
  return null;
}

/** Quando c’è già un bbox in URL: inquadra quell’area (non i marker). */
function FitBbox({ bbox }) {
  const map = useMap();
  useEffect(() => {
    if (!bbox) return;
    const parts = String(bbox).split(",").map(Number);
    if (parts.length !== 4 || parts.some((n) => Number.isNaN(n))) return;
    const [south, west, north, east] = parts;
    map.fitBounds([[south, west], [north, east]], { padding: [24, 24], maxZoom: 16 });
  }, [bbox, map]);
  return null;
}

function ZoomTracker({ onZoom }) {
  const map = useMapEvents({ zoomend: () => onZoom(map.getZoom()) });
  return null;
}

function BoundsWatcher({ onBoundsIdle, suppressOnceRef }) {
  const map = useMapEvents({
    moveend: () => {
      if (suppressOnceRef?.current) {
        suppressOnceRef.current = false;
        return;
      }
      const b = map.getBounds();
      onBoundsIdle?.({
        south: b.getSouth(),
        west: b.getWest(),
        north: b.getNorth(),
        east: b.getEast(),
        zoom: map.getZoom(),
      });
    },
  });
  return null;
}

function FlyToSelected({ selectedId, markers }) {
  const map = useMap();
  useEffect(() => {
    if (!selectedId) return;
    const m = markers.find((x) => x.id === selectedId);
    if (!m?.lat || !m?.lng) return;
    map.panTo([m.lat, m.lng], { animate: true });
  }, [selectedId, markers, map]);
  return null;
}

/**
 * @param {object} props
 * @param {Array} props.markers
 * @param {string|null} props.selectedId
 * @param {(id: string) => void} props.onSelect
 * @param {(bounds: object) => void} props.onBoundsIdle — dopo pan/zoom utente
 * @param {boolean} props.fitOnLoad — fit ai marker al primo carico (no bbox ancora)
 * @param {string} props.bbox — south,west,north,east già applicato
 * @param {string} props.className
 * @param {string} props.heightClass
 */
export default function PropertyMapView({
  markers = [],
  selectedId = null,
  onSelect,
  onBoundsIdle,
  fitOnLoad = true,
  bbox = "",
  className = "",
  heightClass = "h-full min-h-[420px]",
}) {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const mapRef = useRef(null);
  const suppressMoveRef = useRef(true); // ignora moveend iniziale da fitBounds
  const [zoom, setZoom] = useState(DEFAULT_ZOOM);

  const valid = useMemo(() => markers.filter((m) => m.lat && m.lng), [markers]);
  const { clusters, singles } = useMemo(() => clusterMarkers(valid, zoom), [valid, zoom]);

  useEffect(() => {
    // Nuovo set marker (dopo cerca zona): non trattare il prossimo moveend come pan utente
    suppressMoveRef.current = true;
  }, [markers]);

  return (
    <div data-testid="property-map-view" className={`relative ${className} ${heightClass}`}>
      {valid.length === 0 && (
        <div
          data-testid="map-empty-hint"
          className="absolute top-3 left-1/2 -translate-x-1/2 z-[400] bg-white/95 border border-stone-200 rounded-full px-4 py-1.5 text-xs text-stone-700 shadow-sm"
        >
          {t("cloud.map_empty")}
        </div>
      )}
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        scrollWheelZoom
        className="h-full w-full"
        ref={mapRef}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds markers={valid} enabled={fitOnLoad && !bbox} />
        <FitBbox bbox={bbox} />
        <ZoomTracker onZoom={setZoom} />
        <BoundsWatcher onBoundsIdle={onBoundsIdle} suppressOnceRef={suppressMoveRef} />
        <FlyToSelected selectedId={selectedId} markers={valid} />
        {clusters.map((c, i) => (
          <Marker
            key={`cluster-${i}-${c.count}`}
            position={[c.lat, c.lng]}
            icon={clusterIcon(c.count)}
            eventHandlers={{
              click: () => {
                const map = mapRef.current;
                if (map) map.setView([c.lat, c.lng], Math.min(map.getZoom() + 2, CLUSTER_MAX_ZOOM));
              },
            }}
          />
        ))}
        {singles.map((m) => (
          <Marker
            key={m.id}
            position={[m.lat, m.lng]}
            icon={priceIcon(m, selectedId === m.id)}
            eventHandlers={{
              click: () => onSelect?.(m.id),
            }}
            zIndexOffset={selectedId === m.id ? 1000 : 0}
          >
            <Popup>
              <div data-testid={`map-popup-${m.id}`} className="min-w-[180px]">
                <div className="text-sm font-medium text-stone-900 mb-1">
                  {m.title || m.property_type}
                </div>
                <div className="text-xs text-stone-600 mb-1">
                  {m.city}{m.property_type ? ` · ${m.property_type}` : ""}
                </div>
                <div className="text-sm text-[#0B1E3F] font-semibold">
                  {formatPriceFull(m)}
                </div>
                <a
                  href={`/${lang}/cloud/property/${m.id}`}
                  data-testid={`map-popup-link-${m.id}`}
                  className="text-xs uppercase tracking-widest text-[#C19A6B] hover:underline mt-2 inline-block"
                >
                  {t("cloud.view_detail")} →
                </a>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}

export function boundsToBboxParam(b) {
  if (!b) return "";
  return [b.south, b.west, b.north, b.east].map((n) => Number(n).toFixed(5)).join(",");
}
