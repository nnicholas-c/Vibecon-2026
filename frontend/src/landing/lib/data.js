// Loads the opening kit from /drivepast/ with byte progress (PROMPT.md 3.5, 6 Speed).
const BASE = `${process.env.PUBLIC_URL || ""}/drivepast/`;

export const SIZES = {
  meta: 1231,
  fleet: 436432,
  water: 115344,
  surroundings: 167137,
  roads: 302963,
  "buildings-core": 952803,
  "shadows-core": 730673,
  "buildings-rest": 1525876,
  "shadows-rest": 844597,
  sample: 4683,
};

export const FIRST_VIEW = ["meta", "fleet", "water", "surroundings", "roads", "buildings-core", "shadows-core"];

export async function fetchJSON(name, onBytes = () => {}) {
  const res = await fetch(`${BASE}${name}.json`);
  if (!res.ok) throw new Error(`${name}.json ${res.status}`);
  if (!res.body || !res.body.getReader || typeof TextDecoder === "undefined") {
    const j = await res.json();
    onBytes(SIZES[name] || 0);
    return j;
  }
  const reader = res.body.getReader();
  const chunks = [];
  let n = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    n += value.length;
    onBytes(value.length);
  }
  const buf = new Uint8Array(n);
  let o = 0;
  for (const c of chunks) {
    buf.set(c, o);
    o += c.length;
  }
  return JSON.parse(new TextDecoder().decode(buf));
}

// Wait for both fonts to load, or 2.5 seconds, before creating 3D text labels.
export function waitFonts() {
  const f = document.fonts;
  if (!f?.load) return Promise.resolve();
  const all = Promise.all([
    f.load('600 12px "Overpass Mono"'),
    f.load('400 12px "Overpass Mono"'),
    f.load('800 20px "Overpass"'),
    f.load('400 16px "Overpass"'),
  ]).catch(() => {});
  return Promise.race([all, new Promise((r) => setTimeout(r, 2500))]);
}

export function hasWebGL2() {
  try {
    const c = document.createElement("canvas");
    return Boolean(c.getContext("webgl2"));
  } catch {
    return false;
  }
}
