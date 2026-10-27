export const ACCENT = "#FF5B1F";
export const LIGHT_STYLE = "https://tiles.openfreemap.org/styles/positron";

const empty = { type: "geojson", data: { type: "FeatureCollection", features: [] } };
const byState = (sel, normal, dim) => ["match", ["get", "state"], "selected", sel, "dimmed", dim, normal];
const round = { "line-join": "round", "line-cap": "round" };

export const plainStyle = () => ({ version: 8, sources: {}, layers: [{ id: "bg", type: "background", paint: { "background-color": "#F2F1EC" } }] });

export function addRouteLayers(map) {
  if (map.getSource("dp-routes")) return;
  map.addSource("dp-routes", empty);
  map.addSource("dp-proposal", empty);
  map.addSource("dp-ghost", empty);
  map.addLayer({ id: "dp-ghost", type: "line", source: "dp-ghost", layout: round,
    paint: { "line-color": "#141414", "line-width": 2.5, "line-opacity": 0.35, "line-dasharray": [2, 2.5] } });
  map.addLayer({ id: "dp-route-line", type: "line", source: "dp-routes", layout: round,
    paint: { "line-color": ["get", "color"], "line-width": byState(5, 3.6, 2.6), "line-opacity": byState(1, 0.95, 0.3) } });
  map.addLayer({ id: "dp-proposal", type: "line", source: "dp-proposal", layout: round,
    paint: { "line-color": ["get", "color"], "line-width": 3.5, "line-dasharray": [1.5, 2] } });
}

const lum = (hex) => {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
};

// Darken a van color until it has at least 3:1 contrast on the light map.
export function mapColor(hex) {
  let rgb = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  const bg = lum("#F2F1EC");
  const toHex = (a) => `#${a.map((v) => Math.round(v).toString(16).padStart(2, "0")).join("")}`;
  for (let i = 0; i < 20 && (bg + 0.05) / (lum(toHex(rgb)) + 0.05) < 3; i += 1) rgb = rgb.map((v) => v * 0.9);
  return toHex(rgb);
}
