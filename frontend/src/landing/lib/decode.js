// Decoders for the Drivepast opening kit (PROMPT.md section 0).
// lon = o[0] + x / s, lat = o[1] + y / s. Rings in buildings, shadows, roads,
// water and customerBuilding.ring are delta-encoded; everything else is absolute.

export function makeCoder(meta) {
  const [ox, oy] = meta.o;
  const s = meta.s;
  return { lon: (x) => ox + x / s, lat: (y) => oy + y / s };
}

// Delta ring -> list of [lon, lat] (or [lon, lat, z])
export function deltaRing(ring, c, z) {
  const out = [];
  let x = 0;
  let y = 0;
  for (let i = 0; i < ring.length; i += 2) {
    x += ring[i];
    y += ring[i + 1];
    out.push(z === undefined ? [c.lon(x), c.lat(y)] : [c.lon(x), c.lat(y), z]);
  }
  return out;
}

// Delta ring -> flat XYZ Float64Array
export function deltaFlat(ring, c, z) {
  const n = ring.length / 2;
  const out = new Float64Array(n * 3);
  let x = 0;
  let y = 0;
  for (let i = 0; i < n; i++) {
    x += ring[i * 2];
    y += ring[i * 2 + 1];
    out[i * 3] = c.lon(x);
    out[i * 3 + 1] = c.lat(y);
    out[i * 3 + 2] = z;
  }
  return out;
}

export const absPoint = (p, c) => [c.lon(p[0]), c.lat(p[1])];

export function absPath(flat, c) {
  const out = [];
  for (let i = 0; i < flat.length; i += 2) out.push([c.lon(flat[i]), c.lat(flat[i + 1])]);
  return out;
}

export const decodeBuildings = (list, c) => list.map((b) => ({ h: b[0], p: deltaFlat(b[2], c, 0) }));

export const decodeShadows = (list, c) =>
  list.map((poly) => (poly.length === 1 ? deltaFlat(poly[0], c, 0.5) : poly.map((r) => deltaRing(r, c, 0.5))));

export const decodeRoads = (list, c) => list.map(([k, ring]) => ({ k, p: deltaFlat(ring, c, 0.25) }));

// Water: polygons, first ring the outline, the rest holes (FIXES.md).
export const decodeWater = (list, c) => list.map((poly) => (poly.length === 1 ? deltaFlat(poly[0], c, 0) : poly.map((r) => deltaRing(r, c, 0))));

// Surroundings: absolute ground corners, delta-encoded road rings.
export function decodeSurroundings(s, c) {
  const [[x0, y0], [x1, y1]] = s.ground;
  return { ground: [c.lon(x0), c.lat(y0), c.lon(x1), c.lat(y1)], roads: decodeRoads(s.roads, c) };
}

export function decodeFleet(fleet, c) {
  return fleet.vans.map((v) => ({
    id: v.id,
    loop: v.loop,
    ts: v.ts,
    path: absPath(v.path, c),
    stops: v.stops.map((p) => absPoint(p, c)),
  }));
}

export function decodeMeta(meta) {
  const c = makeCoder(meta);
  const cb = meta.customerBuilding;
  const [x0, y0, x1, y1] = meta.slab;
  return {
    raw: meta,
    coder: c,
    slab: [c.lon(x0), c.lat(y0), c.lon(x1), c.lat(y1)],
    building: { h: cb.h, ring: deltaRing(cb.ring, c, 0), center: absPoint(cb.center, c), door: absPoint(cb.door, c) },
    street: absPoint(meta.customer.street, c),
    passTime: meta.customer.passTime,
    window: meta.customer.window,
    places: meta.places,
    counts: meta.counts,
  };
}

// Checks the decoder against sample.json's "expected" block. Returns a list of failures.
export function checkSample(sample, meta) {
  const c = makeCoder(meta);
  const m = decodeMeta(meta);
  const ex = sample.expected;
  const fails = [];
  const near = (a, b, label) => {
    if (Math.abs(a[0] - b[0]) > 1e-6 || Math.abs(a[1] - b[1]) > 1e-6) fails.push(`${label}: got ${a} want ${b}`);
  };
  const b0 = deltaRing(sample.buildings[0][2], c);
  ex["buildings[0]"].firstPoints.forEach((p, i) => near(b0[i], p, `building point ${i}`));
  if (b0.length !== ex["buildings[0]"].pointCount) fails.push("building point count");
  if (sample.buildings[0][0] !== ex["buildings[0]"].height) fails.push("building height");
  const s0 = sample.shadows[0].map((r) => deltaRing(r, c));
  if (s0.length !== ex["shadows[0]"].rings) fails.push("shadow ring count");
  ex["shadows[0]"].firstPoints.forEach((p, i) => near(s0[0][i], p, `shadow point ${i}`));
  const r0 = deltaRing(sample.roads[0][1], c);
  if (sample.roads[0][0] !== ex["roads[0]"].class) fails.push("road class");
  ex["roads[0]"].firstPoints.forEach((p, i) => near(r0[i], p, `road point ${i}`));
  const v = absPath(sample.van.path, c);
  ex.van.firstPoints.forEach((p, i) => near(v[i], p, `van point ${i}`));
  ex.van.firstTimes.forEach((t, i) => sample.van.ts[i] !== t && fails.push(`van time ${i}`));
  near(m.building.door, ex.customerDoor, "customer door");
  near(m.street, ex.customerStreetPoint, "street point");
  near(m.building.center, ex.customerCenter, "customer center");
  near(m.slab.slice(0, 2), ex.slab.slice(0, 2), "slab min");
  near(m.slab.slice(2), ex.slab.slice(2), "slab max");
  return fails;
}
