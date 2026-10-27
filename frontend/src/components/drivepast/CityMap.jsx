import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Layers, List, Maximize2, Minus, Plus, RotateCcw } from "lucide-react";
import { Ctl } from "./LeafletRouteMap";
import { LIGHT_STYLE, addRouteLayers, plainStyle } from "./mapStyle";
import { ghostGeo, proposalGeo, requestMarkers, routeGeo, routeState, snapToLine, stopMarkers, vanMarker } from "./cityMarkers";

const PITCH = 55;
const MIN_ZOOM = 13.05;
const TILE_MSG = "Map tiles unavailable";
const DEFAULT_PAD = { paddingTopLeft: [14, 14], paddingBottomRight: [60, 14] };
const reduced = () => Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)").matches);
const coarse = () => Boolean(window.matchMedia?.("(pointer: coarse)").matches);

function pad(fp, node) {
  const [l, t] = fp.paddingTopLeft;
  const [r, b] = fp.paddingBottomRight;
  const w = node.clientWidth;
  return { top: Math.min(t, 40), left: Math.min(l, w * 0.22), right: Math.min(r, w * 0.12), bottom: Math.min(b, 28) };
}

function axisBearing(pts) {
  const lat0 = pts.reduce((a, p) => a + p[1], 0) / pts.length;
  const lon0 = pts.reduce((a, p) => a + p[0], 0) / pts.length;
  const k = Math.cos((lat0 * Math.PI) / 180);
  let sxx = 0; let syy = 0; let sxy = 0;
  pts.forEach(([lo, la]) => { const x = (lo - lon0) * k; const y = la - lat0; sxx += x * x; syy += y * y; sxy += x * y; });
  const theta = (0.5 * Math.atan2(2 * sxy, sxx - syy) * 180) / Math.PI;
  let b = 90 - theta;
  while (b > 90) b -= 180;
  while (b <= -90) b += 180;
  return Math.round(b);
}

function cardBox(node) {
  const card = node.parentElement?.querySelector(".dp-detail-card");
  if (!card) return null;
  const a = node.getBoundingClientRect();
  const b = card.getBoundingClientRect();
  return { r: b.right - a.left + 12, b: b.bottom - a.top + 12 };
}

function camera(map, latlons, fp, node, floor) {
  const w = node.clientWidth;
  const h = node.clientHeight;
  if (!latlons.length || !w || !h) return null;
  const pts = latlons.map(([la, lo]) => [lo, la]);
  const p = pad(fp, node);
  const card = cardBox(node);
  if (card) p.left = 20;
  const box = { l: p.left, r: w - p.right, t: p.top, b: h - p.bottom };
  const saved = { center: map.getCenter(), zoom: map.getZoom(), pitch: map.getPitch(), bearing: map.getBearing() };
  const bearing = floor ? axisBearing(pts) : -15;
  let center = pts.reduce((acc, q) => acc.extend(q), new maplibregl.LngLatBounds()).getCenter();
  let zoom = 12;
  const fits = () => pts.every((q) => { const s = map.project(q); return s.x >= box.l && s.x <= box.r && s.y >= box.t && s.y <= box.b && !(card && s.x < card.r && s.y < card.b); });
  for (let pass = 0; pass < 3; pass += 1) {
    let lo = 9;
    let hi = 16.5;
    for (let i = 0; i < 12; i += 1) {
      const z = (lo + hi) / 2;
      map.jumpTo({ center, zoom: z, pitch: PITCH, bearing });
      if (fits()) lo = z; else hi = z;
    }
    zoom = lo;
    map.jumpTo({ center, zoom, pitch: PITCH, bearing });
    const xs = pts.map((q) => map.project(q));
    const mx = (Math.min(...xs.map((s) => s.x)) + Math.max(...xs.map((s) => s.x))) / 2;
    const my = (Math.min(...xs.map((s) => s.y)) + Math.max(...xs.map((s) => s.y))) / 2;
    const c = map.project(center);
    center = map.unproject([c.x + mx - (box.l + box.r) / 2, c.y + my - (box.t + box.b) / 2]);
  }
  if (floor && zoom < MIN_ZOOM) {
    map.jumpTo({ center, zoom, pitch: PITCH, bearing });
    const around = map.unproject([(box.l + box.r) / 2, (box.t + box.b) / 2]);
    map.zoomTo(MIN_ZOOM, { around, duration: 0, animate: false });
    center = map.getCenter();
    zoom = MIN_ZOOM;
  }
  map.jumpTo(saved);
  return { center, zoom, bearing, pitch: PITCH };
}

const CLOSE_ZOOM = 16.5;
const VAN_M = 5.2;
const vanPx = (map) => {
  const mpp = (40075016.686 * Math.cos((map.getCenter().lat * Math.PI) / 180)) / (512 * 2 ** map.getZoom());
  return Math.max(30, Math.min(64, VAN_M / mpp));
};

function closeUp(map, pos, node) {
  const w = node.clientWidth;
  const h = node.clientHeight;
  if (!w || !h) return null;
  const card = cardBox(node);
  const side = card && card.r < w * 0.7;
  const tx = side ? (card.r + w - 56) / 2 : w / 2;
  const ty = Math.max(h * 0.64, side ? 0 : Math.min((card?.b || 0) + 90, h * 0.8));
  const bearing = pos.heading || 0;
  const saved = { center: map.getCenter(), zoom: map.getZoom(), pitch: map.getPitch(), bearing: map.getBearing() };
  map.jumpTo({ center: [pos.lon, pos.lat], zoom: CLOSE_ZOOM, pitch: PITCH, bearing });
  const center = map.unproject([w - tx, h - ty]);
  map.jumpTo(saved);
  return { center, zoom: CLOSE_ZOOM, pitch: PITCH, bearing };
}

const routePoints = (routes, proposal) => [
  ...routes.flatMap((r) => [r.start_location, ...r.stops, r.end_location].map((p) => [p.lat, p.lon])),
  ...(proposal?.stops || []).map((s) => [s.lat, s.lon]),
];

export default function CityMap({ routes: rawRoutes, proposal, ghost, testId, className = "h-[280px] md:h-[360px]", selectedKey, showRoutes = true, showVans = true, onSelectVan, onList, fitPadding = DEFAULT_PAD, lineNote = "", children, onFail, follow = false }) {
  const routes = useMemo(() => rawRoutes.map(snapToLine), [rawRoutes]);
  const ref = useRef(null);
  const wrap = useRef(null);
  const mapRef = useRef(null);
  const markers = useRef([]);
  const pts = useRef([]);
  const fitSig = useRef("");
  const flown = useRef(false);
  const selectRef = useRef(onSelectVan);
  selectRef.current = onSelectVan;
  const padRef = useRef(fitPadding);
  padRef.current = fitPadding;
  const routesRef = useRef(routes);
  routesRef.current = routes;
  const failRef = useRef(onFail);
  failRef.current = onFail;
  const following = useRef(follow);
  const [ready, setReady] = useState(0);
  const [tileFail, setTileFail] = useState(false);
  const [plain, setPlain] = useState(false);

  const place = (animate) => {
    const map = mapRef.current;
    const pos = follow && !proposal && routesRef.current[0]?.position;
    if (pos && map) return track(map, pos, animate);
    const cam = map && camera(map, pts.current, padRef.current, ref.current, routesRef.current.length === 1);
    if (!cam) return;
    if (!flown.current) {
      flown.current = true;
      if (!animate || reduced()) return map.jumpTo(cam);
      map.jumpTo({ center: cam.center, zoom: cam.zoom - 1.8, pitch: 0, bearing: 0 });
      return map.flyTo({ ...cam, duration: 2400, curve: 1.25, essential: true });
    }
    if (!animate || reduced()) map.jumpTo(cam);
    else map.easeTo({ ...cam, duration: 900 });
  };
  const track = (map, pos, animate) => {
    following.current = true;
    ref.current.dataset.follow = "true";
    const cam = closeUp(map, pos, ref.current);
    if (!cam) return;
    if (!flown.current) {
      flown.current = true;
      if (!animate || reduced()) return map.jumpTo(cam);
      map.jumpTo({ center: [pos.lon, pos.lat], zoom: 13.6, pitch: 20, bearing: 0 });
      return map.flyTo({ ...cam, duration: 2400, curve: 1.3, essential: true });
    }
    if (!animate || reduced()) map.jumpTo(cam);
    else map.easeTo({ ...cam, duration: 900 });
  };
  const unfollow = () => {
    following.current = false;
    if (ref.current) ref.current.dataset.follow = "false";
  };
  const zoomBy = (d) => { unfollow(); mapRef.current?.easeTo({ zoom: mapRef.current.getZoom() + d, duration: reduced() ? 0 : 300 }); };
  const fullscreen = () => (document.fullscreenElement ? document.exitFullscreen() : wrap.current?.requestFullscreen?.());

  useEffect(() => {
    let map;
    try {
      map = new maplibregl.Map({
        container: ref.current, style: LIGHT_STYLE, center: [-122.27, 37.84], zoom: 12, pitch: 0, maxPitch: 70,
        attributionControl: false, cooperativeGestures: coarse(), fadeDuration: 0,
      });
    } catch {
      failRef.current?.();
      return undefined;
    }
    mapRef.current = map;
    ref.current.dpMap = map;
    map.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution: "Routes © OSRM" }), "bottom-right");
    map.once("load", () => ref.current?.querySelector(".maplibregl-compact-show")?.classList.remove("maplibregl-compact-show"));
    const sizeVans = () => ref.current?.style.setProperty("--van-l", `${vanPx(map).toFixed(1)}px`);
    sizeVans();
    map.on("zoom", sizeVans);
    ["dragstart", "zoomstart", "rotatestart", "pitchstart"].forEach((ev) => map.on(ev, (e) => e.originalEvent && unfollow()));
    map.on("wheel", unfollow);
    map.on("moveend", () => {
      const d = ref.current?.dataset;
      if (!d) return;
      d.zoom = map.getZoom().toFixed(2);
      d.pitch = map.getPitch().toFixed(0);
      d.bearing = map.getBearing().toFixed(0);
    });
    let gotTile = false;
    let fellBack = false;
    map.on("sourcedata", (e) => {
      if (e.tile && !String(e.sourceId).startsWith("dp-") && !gotTile) { gotTile = true; setTileFail(false); }
    });
    map.on("error", (e) => {
      if (gotTile) return;
      setTileFail(true);
      if (!fellBack && !map.isStyleLoaded()) { fellBack = true; map.setStyle(plainStyle()); }
    });
    map.on("webglcontextlost", () => failRef.current?.());
    const timer = setTimeout(() => !gotTile && setTileFail(true), 12000);
    map.on("style.load", () => {
      addRouteLayers(map);
      setReady((n) => n + 1);
    });
    let lastW = ref.current.offsetWidth;
    const ro = new ResizeObserver(() => {
      const w = ref.current?.offsetWidth || 0;
      map.resize();
      if (w && !lastW) place(false);
      lastW = w;
    });
    ro.observe(ref.current);
    return () => { clearTimeout(timer); ro.disconnect(); map.remove(); mapRef.current = null; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!ready) return;
    const started = performance.now();
    const map = mapRef.current;
    const visible = showRoutes ? routes : [];
    map.getSource("dp-routes").setData(routeGeo(visible, selectedKey));
    map.getSource("dp-proposal").setData(proposalGeo(proposal));
    map.getSource("dp-ghost")?.setData(ghostGeo(ghost));
    ref.current.dataset.ghost = ghost ? "on" : "off";
    markers.current.forEach((m) => m.remove());
    const next = [...visible.flatMap((r) => stopMarkers(r, selectedKey)), ...requestMarkers(proposal)];
    if (showVans) routes.forEach((r) => { const m = vanMarker(r, selectedKey, (k) => selectRef.current?.(k), !follow); if (m) next.push(m); });
    next.forEach((m) => m.addTo(map));
    markers.current = next;
    ref.current.dataset.drawnMs = String(Math.round(performance.now() - started));
    ref.current.dataset.drawn = "true";
  }, [ready, routes, proposal, ghost, selectedKey, showRoutes, showVans, follow]);

  const posKey = follow ? JSON.stringify(routes[0]?.position || null) : "";
  useEffect(() => {
    if (!ready || !follow || !flown.current || !following.current || !routes[0]?.position) return;
    track(mapRef.current, routes[0].position, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [posKey]);

  useEffect(() => {
    if (!ready) return;
    pts.current = routePoints(routes, proposal);
    const sig = pts.current.map((p) => p.join(",")).join("|");
    if (!sig || sig === fitSig.current) return;
    fitSig.current = sig;
    if (follow && flown.current && !proposal) return;
    place(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, routes, proposal]);

  return (
    <div className="space-y-2">
      <div ref={wrap} className={`dp-map dp-map-3d ${plain ? "is-plain" : ""} ${className}`} data-testid={testId} data-engine="maplibre">
        <div ref={ref} className="h-full w-full" data-testid={`${testId}-canvas`} />
        <div className="sr-only" data-testid={`${testId}-routes`}>
          {showRoutes && routes.map((r) => (
            <span key={r.unit_key} data-testid={`map-route-${r.unit_key}`} data-state={routeState(r, selectedKey)} data-lines={r.geometry ? "streets" : "straight"}>{r.name}</span>
          ))}
        </div>
        <div className="dp-map-ctls" data-testid={`${testId}-controls`}>
          {onList && <Ctl icon={List} label="Jump to the list" onClick={onList} testId={`${testId}-list`} />}
          <Ctl icon={Plus} label="Zoom in" onClick={() => zoomBy(1)} testId={`${testId}-zoom-in`} />
          <Ctl icon={Minus} label="Zoom out" onClick={() => zoomBy(-1)} testId={`${testId}-zoom-out`} />
          <Ctl icon={RotateCcw} label="Fit the route" onClick={() => place(true)} testId={`${testId}-reset`} />
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
          <div className="dp-tiles-note" data-testid="map-tiles-error" role="status">{TILE_MSG}</div>
        )}
      </div>
      <p className="flex justify-between gap-3 px-1 text-xs text-[var(--dp-ink-3)]" data-testid={`${testId}-hint`}>
        <span>Drag to pan · Right-drag to tilt · Scroll to zoom</span>
        <span>Updates when the route changes</span>
      </p>
    </div>
  );
}
