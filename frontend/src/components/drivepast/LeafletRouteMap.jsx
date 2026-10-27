import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Layers, List, Maximize2, Minus, Plus, RotateCcw } from "lucide-react";
import { pinLabel } from "./cityMarkers";

const TILE_MSG = "Map tiles couldn't load. Routes are still shown.";
export const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

export function icon(inner, cls, color, testId, w = 24) {
  return L.divIcon({
    html: `<div class="${cls}" style="--pin:${color}" data-testid="${testId}">${inner}</div>`,
    className: "", iconSize: [w, 24], iconAnchor: [w / 2, 12], popupAnchor: [0, -12],
  });
}

export function popup(s, label) {
  const tag = label ? `<span style="display:inline-block;margin-bottom:4px;padding:1px 8px;background:#FF5B1F;color:#141414;font-size:11px;font-weight:700">${label}</span><br/>` : "";
  return `<div style="font-size:13px;line-height:1.45">${tag}<strong>${esc(s.name)}</strong><br/>${esc(s.address)}<br/>`
    + `<span style="font-variant-numeric:tabular-nums">Arrives ${esc(s.arrival_label)}${s.window_label ? `<br/>Window ${esc(s.window_label)}` : ""}</span></div>`;
}

const LIME = "#FF5B1F";
const vanSvg = (color) => `<svg viewBox="0 0 32 32" width="30" height="30" aria-hidden="true"><rect x="9" y="3" width="14" height="26" rx="4.5" fill="#f4f4f5" stroke="${color}" stroke-width="2"/><rect x="11" y="6" width="10" height="5" rx="1.5" fill="#111214"/><rect x="11" y="13.5" width="10" height="12.5" rx="1.5" fill="${color}" opacity=".6"/><rect x="7" y="8" width="2" height="3" rx="1" fill="#f4f4f5"/><rect x="23" y="8" width="2" height="3" rx="1" fill="#f4f4f5"/></svg>`;

function drawRoute(layer, r, bounds, sel, showRoutes, animate) {
  const pts = [r.start_location, ...r.stops, r.end_location].map((p) => [p.lat, p.lon]);
  bounds.push(...pts);
  if (!showRoutes) return;
  const on = sel === r.unit_key;
  const dim = Boolean(sel) && !on;
  const state = on ? "selected" : dim ? "dimmed" : "normal";
  const line = L.polyline(r.geometry || pts, { color: on ? LIME : r.color, weight: on ? 4 : 3, opacity: dim ? 0.18 : 0.92, className: `dp-route-line is-${state}${animate ? " dp-route" : ""}` });
  line.on("add", () => {
    const el = line.getElement();
    el?.setAttribute("pathLength", "1");
    el?.setAttribute("data-testid", `map-route-${r.unit_key}`);
    el?.setAttribute("data-state", state);
    el?.setAttribute("data-lines", r.geometry ? "streets" : "straight");
  });
  line.addTo(layer);
  L.marker([r.start_location.lat, r.start_location.lon], { icon: icon("", "dp-depot", r.color, `map-depot-${r.unit_key}`, 22), zIndexOffset: -100, opacity: dim ? 0.35 : 1 })
    .bindPopup(`<strong>${esc(r.start_location.name)}</strong><br/>Start and end of ${esc(r.name)}`).addTo(layer);
  r.stops.forEach((s) => {
    const moved = s.old_seq && s.old_seq !== s.seq ? " is-moved" : "";
    L.marker([s.lat, s.lon], { icon: icon(pinLabel(s), `dp-pin${s.is_new ? " is-new" : ""}${s.done ? " is-done" : ""}${moved}`, on ? LIME : r.color, `map-marker-${r.unit_key}-${s.seq}`), opacity: dim ? 0.35 : 1 })
      .bindPopup(popup(s, s.is_new ? "New" : "")).addTo(layer);
  });
}

function drawVan(layer, r, sel, onSelect) {
  const p = r.position;
  if (!p) return;
  const on = sel === r.unit_key;
  const html = `<div class="dp-van${on ? " is-selected" : ""}" data-testid="map-van-${r.unit_key}" data-heading="${p.heading}"><span class="dp-van-halo"></span><span class="dp-van-body" style="transform:rotate(${p.heading}deg)">${vanSvg(r.color)}</span></div>`;
  L.marker([p.lat, p.lon], { icon: L.divIcon({ html, className: "", iconSize: [44, 44], iconAnchor: [22, 22] }), zIndexOffset: on ? 20000 : 10000, title: r.name })
    .on("click", () => onSelect(r.unit_key)).addTo(layer);
}

function drawProposal(map, p, bounds) {
  p.paths.forEach((path) => L.polyline(path, { color: p.color, weight: 3, opacity: 0.95, dashArray: "6 8", className: "dp-proposal" }).addTo(map));
  p.stops.forEach((s, i) => {
    bounds.push([s.lat, s.lon]);
    L.marker([s.lat, s.lon], { icon: icon("New request", "dp-pin is-request", p.color, `map-request-pin-${i}`, 92), zIndexOffset: 500 })
      .bindPopup(popup(s, "New request")).addTo(map);
  });
}

const DEFAULT_PAD = { paddingTopLeft: [14, 14], paddingBottomRight: [60, 14] };

export function Ctl({ icon: Icon, label, onClick, testId, active }) {
  return (
    <button type="button" title={label} aria-label={label} onClick={onClick} data-testid={testId} className={`dp-map-ctl${active ? " is-on" : ""}`}>
      <Icon className="h-4 w-4" />
    </button>
  );
}

export default function LeafletRouteMap({ routes, proposal, ghost, testId, className = "h-[280px] md:h-[360px]", selectedKey, showRoutes = true, showVans = true, onSelectVan, onList, fitPadding = DEFAULT_PAD, lineNote = "", children }) {
  const ref = useRef(null);
  const wrap = useRef(null);
  const mapRef = useRef(null);
  const layerRef = useRef(null);
  const fitRef = useRef([]);
  const firstDraw = useRef(true);
  const selectRef = useRef(onSelectVan);
  selectRef.current = onSelectVan;
  const padRef = useRef(fitPadding);
  padRef.current = fitPadding;
  const [tileFail, setTileFail] = useState(false);
  const [plain, setPlain] = useState(false);
  const fitAll = () => fitRef.current.length && mapRef.current?.fitBounds(fitRef.current, padRef.current);
  const fullscreen = () => (document.fullscreenElement ? document.exitFullscreen() : wrap.current?.requestFullscreen?.());

  useEffect(() => {
    const map = L.map(ref.current, { scrollWheelZoom: false, dragging: !L.Browser.mobile, tap: false, touchZoom: true, zoomControl: false, keyboard: false, zoomSnap: 0.25 });
    map.attributionControl.setPrefix(false);
    const fit = fitRef.current;
    let loaded = 0;
    let failed = 0;
    const tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "© OpenStreetMap contributors · Routes © OSRM" });
    tiles.on("tileload", () => { loaded += 1; setTileFail(false); });
    tiles.on("tileerror", () => { failed += 1; if (!loaded && failed >= 2) setTileFail(true); });
    tiles.addTo(map);
    map.on("click", () => map.scrollWheelZoom.enable());
    map.on("mouseout", () => map.scrollWheelZoom.disable());
    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;
    let lastW = ref.current.offsetWidth;
    let lastH = ref.current.offsetHeight;
    const ro = new ResizeObserver(() => {
      const w = ref.current?.offsetWidth || 0;
      const h = ref.current?.offsetHeight || 0;
      if (w && (w !== lastW || h !== lastH)) {
        map.invalidateSize();
        if (!lastW && fitRef.current.length) map.fitBounds(fitRef.current, padRef.current);
      }
      lastW = w;
      lastH = h;
    });
    ro.observe(ref.current);
    return () => { ro.disconnect(); map.remove(); mapRef.current = null; };
  }, []);

  useEffect(() => {
    const started = performance.now();
    const layer = layerRef.current;
    layer.clearLayers();
    const bounds = [];
    if (ghost) L.polyline(ghost.path, { color: "#141414", weight: 2.5, opacity: 0.35, dashArray: "6 8", className: "dp-ghost" }).addTo(layer);
    routes.forEach((r) => drawRoute(layer, r, bounds, selectedKey, showRoutes, firstDraw.current));
    if (proposal) drawProposal(layer, proposal, bounds);
    if (showVans) routes.forEach((r) => drawVan(layer, r, selectedKey, (k) => selectRef.current?.(k)));
    fitRef.current = bounds;
    firstDraw.current = false;
    ref.current.dataset.drawnMs = String(Math.round(performance.now() - started));
    ref.current.dataset.drawn = "true";
    ref.current.dataset.ghost = ghost ? "on" : "off";
  }, [routes, proposal, ghost, selectedKey, showRoutes, showVans]);

  useEffect(() => {
    if (fitRef.current.length) mapRef.current.fitBounds(fitRef.current, padRef.current);
  }, [routes, proposal]);

  return (
    <div className="space-y-2">
      <div ref={wrap} className={`dp-map ${plain ? "is-plain" : ""} ${className}`} data-testid={testId}>
        <div ref={ref} className="h-full w-full" data-testid={`${testId}-canvas`} />
        <div className="dp-map-ctls" data-testid={`${testId}-controls`}>
          {onList && <Ctl icon={List} label="Jump to the list" onClick={onList} testId={`${testId}-list`} />}
          <Ctl icon={Plus} label="Zoom in" onClick={() => mapRef.current?.zoomIn()} testId={`${testId}-zoom-in`} />
          <Ctl icon={Minus} label="Zoom out" onClick={() => mapRef.current?.zoomOut()} testId={`${testId}-zoom-out`} />
          <Ctl icon={RotateCcw} label="Fit the route" onClick={fitAll} testId={`${testId}-reset`} />
          <Ctl icon={Maximize2} label="Full screen" onClick={fullscreen} testId={`${testId}-fullscreen`} />
          <Ctl icon={Layers} label={plain ? "Dark map" : "Light map"} onClick={() => setPlain((v) => !v)} testId={`${testId}-layers`} active={plain} />
        </div>
        {children}
        {lineNote && (
          <div className="absolute bottom-8 left-3 z-[600] rounded-full bg-[var(--dp-surface)] px-3 py-1.5 text-xs text-[var(--dp-ink-2)]" data-testid={`${testId}-lines-note`} role="status">
            {lineNote}
          </div>
        )}
        {tileFail && (
          <div className="absolute inset-x-3 top-3 z-[500] rounded-lg bg-[var(--dp-amber-soft)] px-3 py-2 text-sm text-[var(--dp-amber)]" data-testid="map-tiles-error" role="status">
            {TILE_MSG}
          </div>
        )}
      </div>
      <p className="flex justify-between gap-3 px-1 text-xs text-[var(--dp-ink-3)]">
        <span>Click the map, then scroll to zoom</span>
        <span>Updates when the route changes</span>
      </p>
    </div>
  );
}
