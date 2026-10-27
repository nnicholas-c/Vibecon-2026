import maplibregl from "maplibre-gl";
import { esc, popup } from "./LeafletRouteMap";
import { ACCENT, mapColor } from "./mapStyle";

const VAN_IMG = `${process.env.PUBLIC_URL || ""}/assets/van-topdown.png`;
const ll = (p) => [p.lon, p.lat];

function el(html) {
  const d = document.createElement("div");
  d.innerHTML = html;
  return d.firstElementChild;
}

const pop = (html) => new maplibregl.Popup({ offset: 16, className: "dp-popup", maxWidth: "260px" }).setHTML(html);

export function routeState(r, sel) {
  const on = sel === r.unit_key;
  return on ? "selected" : sel ? "dimmed" : "normal";
}

export function routeCoords(r) {
  const pts = r.geometry || [r.start_location, ...r.stops, r.end_location].map((p) => [p.lat, p.lon]);
  return pts.map(([la, lo]) => [lo, la]);
}

export function routeGeo(routes, sel) {
  return {
    type: "FeatureCollection",
    features: routes.map((r) => {
      const state = routeState(r, sel);
      return { type: "Feature", properties: { key: r.unit_key, state, color: state === "selected" ? ACCENT : mapColor(r.color) }, geometry: { type: "LineString", coordinates: routeCoords(r) } };
    }),
  };
}

export function ghostGeo(g) {
  const features = g ? [{ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: g.path.map(([la, lo]) => [lo, la]) } }] : [];
  return { type: "FeatureCollection", features };
}

export const pinLabel = (s) => (s.done ? "✓" : s.old_seq && s.old_seq !== s.seq
  ? `<span class="dp-pin-old">${s.old_seq}</span><span class="dp-pin-new">${s.seq}</span>` : `${s.seq}`);

export function proposalGeo(p) {
  const features = (p?.paths || []).map((path) => ({ type: "Feature", properties: { color: p.color }, geometry: { type: "LineString", coordinates: path.map(([la, lo]) => [lo, la]) } }));
  return { type: "FeatureCollection", features };
}

export function stopMarkers(r, sel) {
  const state = routeState(r, sel);
  const color = state === "selected" ? ACCENT : mapColor(r.color);
  const opacity = state === "dimmed" ? "0.35" : "1";
  const depot = el(`<div class="dp-depot" style="--pin:${mapColor(r.color)}" data-testid="map-depot-${r.unit_key}"></div>`);
  const out = [new maplibregl.Marker({ element: depot, opacity }).setLngLat(ll(r.start_location)).setPopup(pop(`<strong>${esc(r.start_location.name)}</strong><br/>Start and end of ${esc(r.name)}`))];
  r.stops.forEach((s) => {
    const pin = el(`<div class="dp-pin dp-pin3d${s.is_new ? " is-new" : ""}${s.done ? " is-done" : ""}${s.old_seq && s.old_seq !== s.seq ? " is-moved" : ""}" style="--pin:${color}" data-testid="map-marker-${r.unit_key}-${s.seq}" data-done="${s.done ? "true" : "false"}">${pinLabel(s)}</div>`);
    out.push(new maplibregl.Marker({ element: pin, opacity }).setLngLat(ll(s)).setPopup(pop(popup(s, s.is_new ? "New" : ""))));
  });
  return out;
}

export function requestMarkers(p) {
  return (p?.stops || []).map((s, i) => {
    const pin = el(`<div class="dp-pin is-request" style="--pin:${p.color}" data-testid="map-request-pin-${i}">New request</div>`);
    return new maplibregl.Marker({ element: pin }).setLngLat(ll(s)).setPopup(pop(popup(s, "New request")));
  });
}

const miniSvg = (color) => `<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M8 0.5 11.2 5.2H4.8Z" fill="#f4f4f5"/><circle cx="8" cy="10" r="4.6" fill="${color}" stroke="#111214" stroke-width="1.6"/></svg>`;

export function snapToLine(r) {
  const p = r.position;
  const g = r.geometry;
  if (!p || !g || g.length < 2) return r;
  const k = Math.cos((p.lat * Math.PI) / 180) * 111320;
  const toXY = ([la, lo]) => [(lo - p.lon) * k, (la - p.lat) * 110540];
  let best = null;
  for (let i = 0; i < g.length - 1; i += 1) {
    const [ax, ay] = toXY(g[i]);
    const [bx, by] = toXY(g[i + 1]);
    const dx = bx - ax;
    const dy = by - ay;
    const len = dx * dx + dy * dy;
    const t = len ? Math.max(0, Math.min(1, -(ax * dx + ay * dy) / len)) : 0;
    const x = ax + t * dx;
    const y = ay + t * dy;
    const d = x * x + y * y;
    if (len && (!best || d < best.d)) best = { d, x, y, heading: (Math.atan2(dx, dy) * 180) / Math.PI };
  }
  if (!best || best.d > 800 * 800) return r;
  const position = { ...p, lat: p.lat + best.y / 110540, lon: p.lon + best.x / k, heading: Math.round((best.heading + 360) % 360) };
  return { ...r, position };
}

export function vanMarker(r, sel, onSelect, compact) {
  const p = r.position;
  if (!p) return null;
  const on = sel === r.unit_key;
  const attrs = `data-testid="map-van-${r.unit_key}" data-heading="${p.heading}" title="${esc(r.name)}"`;
  const node = compact
    ? el(`<div class="dp-van-mini${on ? " is-selected" : ""}" ${attrs}><span class="dp-van-mini-halo"></span>${miniSvg(mapColor(r.color))}</div>`)
    : el(`<div class="dp-van3d${on ? " is-selected" : ""}" ${attrs}><span class="dp-van3d-halo"></span>`
      + `<img class="dp-van-img" src="${VAN_IMG}" alt="${esc(r.name)}" draggable="false"/><span class="dp-van-dot" style="background:${mapColor(r.color)}"></span></div>`);
  node.addEventListener("click", (e) => { e.stopPropagation(); onSelect(r.unit_key); });
  return new maplibregl.Marker({ element: node, rotation: p.heading || 0, rotationAlignment: "map", pitchAlignment: "map" }).setLngLat(ll(p));
}
