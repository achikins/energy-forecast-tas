/**
 * TasmaniaMap — Mapbox GL map of Tasmanian energy infrastructure.
 *
 * Marker types use clean SVG icons (no emoji):
 *   Hydro       — water drop      (blue)
 *   Wind        — turbine blades  (green)
 *   Substation  — lightning bolt  (purple)
 *   Interconnect— network node    (amber)
 *
 * Features:
 *   - Click any marker for a popup with specs
 *   - Legend toggles each type on/off
 *   - Live demand + peak overlay drawn from /insights API
 */

import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

import { INFRASTRUCTURE, TYPE_STYLE } from "../../data/infrastructure";

const TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

const TAS_BOUNDS = [
  [143.6, -43.8],
  [148.6, -39.6],
];

const TYPES = [
  { key: "hydro",        label: "Hydro Generation" },
  { key: "wind",         label: "Wind Generation" },
  { key: "substation",   label: "Substation" },
  { key: "interconnect", label: "Interconnector" },
];

function formatMW(val) {
  return val != null ? `${val.toLocaleString()} MW` : null;
}

// ── SVG icons for the React legend (inline, colour-aware) ────────────────────

function HydroIcon({ color }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2C6 9 4 13 4 16a8 8 0 0 0 16 0c0-3-2-7-8-14z" />
    </svg>
  );
}

function WindIcon({ color }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 12L8 4" /><path d="M12 12L4 16" /><path d="M12 12l8 0" />
      <circle cx="12" cy="12" r="2" fill={color} stroke="none" />
      <line x1="12" y1="14" x2="12" y2="22" />
    </svg>
  );
}

function SubstationIcon({ color }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  );
}

function InterconnectIcon({ color }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" />
      <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
      <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
    </svg>
  );
}

const LEGEND_ICON = {
  hydro:        HydroIcon,
  wind:         WindIcon,
  substation:   SubstationIcon,
  interconnect: InterconnectIcon,
};

// ── Main component ───────────────────────────────────────────────────────────

export default function TasmaniaMap({ currentDemandMw, peakDemandMw }) {
  const containerRef = useRef(null);
  const mapRef       = useRef(null);
  const markersRef   = useRef([]);

  const [visibleTypes, setVisibleTypes] = useState(
    Object.fromEntries(TYPES.map((t) => [t.key, true]))
  );

  // ── Init map ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!TOKEN || mapRef.current) return;

    mapboxgl.accessToken = TOKEN;

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/dark-v11",
      bounds: TAS_BOUNDS,
      fitBoundsOptions: { padding: 48 },
      attributionControl: false,
    });

    map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), "bottom-right");
    map.addControl(new mapboxgl.AttributionControl({ compact: true }), "bottom-left");

    map.on("load", () => addMarkers(map, visibleTypes));

    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Redraw on filter change ─────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.loaded()) return;
    clearMarkers();
    addMarkers(map, visibleTypes);
  }, [visibleTypes]);

  function clearMarkers() {
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];
  }

  function addMarkers(map, visible) {
    INFRASTRUCTURE
      .filter((site) => visible[site.type])
      .forEach((site) => {
        const style = TYPE_STYLE[site.type];

        // ── Marker element — pill with SVG icon ────────────────────
        const el = document.createElement("div");
        el.className = "map-marker";
        el.style.setProperty("--mc", style.color);
        el.innerHTML = style.svg;

        // ── Popup HTML ──────────────────────────────────────────────
        const typeLabel = site.type.charAt(0).toUpperCase() + site.type.slice(1);
        const capacityRow = site.capacity_mw
          ? `<div class="pu-row">
               <span class="pu-key">Capacity</span>
               <span class="pu-val" style="color:${style.color}">${formatMW(site.capacity_mw)}</span>
             </div>`
          : "";

        const popup = new mapboxgl.Popup({
          offset: 22,
          maxWidth: "268px",
          className: "energy-popup",
        }).setHTML(`
          <div class="pu-wrap">
            <div class="pu-stripe" style="background:${style.color}"></div>
            <div class="pu-body">
              <div class="pu-head">
                <div class="pu-icon-wrap" style="background:${style.color}22;border-color:${style.color}44">
                  <span style="color:${style.color};display:flex">${style.svg}</span>
                </div>
                <div>
                  <div class="pu-name">${site.name}</div>
                  <div class="pu-type">${typeLabel}</div>
                </div>
              </div>
              ${capacityRow}
              <div class="pu-desc">${site.description}</div>
            </div>
          </div>
        `);

        const marker = new mapboxgl.Marker({ element: el, anchor: "center" })
          .setLngLat(site.coords)
          .setPopup(popup)
          .addTo(map);

        markersRef.current.push(marker);
      });
  }

  function toggleType(key) {
    setVisibleTypes((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  // ── No token ────────────────────────────────────────────────────────
  if (!TOKEN) {
    return (
      <div className="map-token-missing">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
        </svg>
        <div className="map-token-title">Mapbox token required</div>
        <div className="map-token-body">
          Create <code>frontend/.env</code> and add:<br />
          <code>VITE_MAPBOX_TOKEN=pk.your_token_here</code>
          <br /><br />
          Free at <strong>mapbox.com</strong> — 50k loads/month.
        </div>
      </div>
    );
  }

  return (
    <div className="map-wrapper">
      <div ref={containerRef} className="map-container" />

      {/* ── Demand overlay ── */}
      <div className="map-demand-overlay">
        <div className="map-demand-label">Avg Demand</div>
        <div className="map-demand-value">
          {currentDemandMw != null
            ? currentDemandMw.toLocaleString(undefined, { maximumFractionDigits: 0 })
            : "—"}
          <span>MW</span>
        </div>
        {peakDemandMw != null && (
          <div className="map-demand-peak">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{marginRight:4}}>
              <polyline points="18 15 12 9 6 15"/>
            </svg>
            Peak {peakDemandMw.toLocaleString(undefined, { maximumFractionDigits: 0 })} MW
          </div>
        )}
        <div className="map-demand-region">TAS1 · NEM</div>
      </div>

      {/* ── Legend ── */}
      <div className="map-legend">
        <div className="map-legend-title">Infrastructure</div>
        {TYPES.map(({ key, label }) => {
          const style = TYPE_STYLE[key];
          const active = visibleTypes[key];
          const Icon = LEGEND_ICON[key];
          return (
            <button
              key={key}
              className={`map-legend-item ${active ? "" : "map-legend-item--off"}`}
              onClick={() => toggleType(key)}
              style={{ "--lc": style.color }}
            >
              <span className="map-legend-icon-wrap">
                <Icon color={active ? style.color : "var(--text-muted)"} />
              </span>
              <span>{label}</span>
              {active && <span className="map-legend-check">✓</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
