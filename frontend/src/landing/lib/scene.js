// The 3D scene (PROMPT.md section 4 and 5). Imperative: one rAF loop, per-frame values in fields.
import { Camera, flight, fromMerc } from "./camera";
import { RGB } from "./constants";
import { decodeBuildings, decodeShadows } from "./decode";
import { clamp, easeInOutCubic, easeOutCubic, fmtClock, liftAt, ramp, rulerPct, storyClock } from "./story";
import { buildVanMesh } from "./vanMesh";

const FLAT = { depthWriteEnabled: false, depthCompare: "always" };
const ON_TOP = { depthCompare: "always" };
const MAT_B = { ambient: 0.78, diffuse: 0.36, shininess: 12, specularColor: [16, 16, 16] };
const MAT_V = { ambient: 0.62, diffuse: 0.62, shininess: 48, specularColor: [90, 90, 90] };
const ACC = RGB.accent;
const MONO = '"Overpass Mono", ui-monospace, monospace';
const TV_Z = (t) => (t - 30) * 6;
const zMatrix = (s) => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, s, 0, 0, 0, 0, 1];

// Position and heading of a van at story time t (binary search + linear interpolation)
function vanAt(v, t) {
  const ts = v.ts;
  const n = ts.length;
  let i;
  if (t <= ts[0]) i = 0;
  else if (t >= ts[n - 1]) i = n - 2;
  else {
    let lo = 0;
    let hi = n - 1;
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1;
      if (ts[mid] <= t) lo = mid;
      else hi = mid;
    }
    i = lo;
  }
  const a = v.path[i];
  const b = v.path[i + 1];
  const u = clamp((t - ts[i]) / Math.max(1e-6, ts[i + 1] - ts[i]));
  const east = (b[0] - a[0]) * Math.cos((a[1] * Math.PI) / 180);
  const north = b[1] - a[1];
  if (Math.abs(east) + Math.abs(north) > 1e-7) v.heading = (Math.atan2(north, east) * 180) / Math.PI;
  return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u];
}

function flatPath(points, z) {
  const out = new Float64Array(points.length * 3);
  points.forEach((p, i) => {
    out[i * 3] = p[0];
    out[i * 3 + 1] = p[1];
    out[i * 3 + 2] = typeof z === "function" ? z(i) : z;
  });
  return out;
}

function ribbon(v) {
  const pts = [];
  const zs = [];
  const add = (t) => {
    pts.push(vanAt(v, t));
    zs.push(TV_Z(t));
  };
  add(30);
  v.ts.forEach((t) => t > 30 && t < 210 && add(t));
  add(210);
  return { p: flatPath(pts, (i) => zs[i]), v2: v.id === 2 };
}

const offsetM = ([lon, lat], east, north) => [lon + east / (111320 * Math.cos((lat * Math.PI) / 180)), lat + north / 110540];

export class Scene {
  constructor({ D, canvas, data, phone, reduced, ui, getP, onReady, onError, onSign }) {
    Object.assign(this, { D, canvas, data, phone, reduced, ui, getP, onReady, onError, onSign });
    this.introAt = null;
    this.hero = 30;
    this.last = 0;
    this.lastUI = 0;
    this.signOn = false;
    this.ready = false;
    this.degraded = false;
    this.perf = { sum: 0, n: 0, t0: 0 };
    this.rest = null;
    const m = data.meta;
    this.cam = new Camera(D.WebMercatorViewport, { center: m.building.center, door: m.building.door, street: m.street });
    this.vans = data.fleet;
    this.van2 = this.vans.find((v) => v.id === 2);
    this.mesh = buildVanMesh();
    this.buildStatic();
    const lighting = new D.LightingEffect({
      ambient: new D.AmbientLight({ color: [242, 245, 255], intensity: 1.0 }),
      sun: new D.DirectionalLight({ color: [255, 250, 240], intensity: 1.0, direction: [0.227, 0.743, -0.629] }),
    });
    this.dpr = Math.min(1.5, window.devicePixelRatio || 1);
    this.deck = new D.Deck({
      canvas,
      width: "100%",
      height: "100%",
      views: new D.MapView({ id: "map", farZMultiplier: 10 }),
      controller: false,
      useDevicePixels: this.dpr,
      viewState: this.viewState(this.cam.intro(window.innerWidth, window.innerHeight, phone)),
      layers: [],
      effects: [lighting],
      onError: (e) => this.fail(e),
      onAfterRender: () => {
        if (!this.ready && this.frames > 2) {
          this.ready = true;
          onReady?.();
        }
      },
    });
    this.frames = 0;
    window.__lpScene = this;
    this.tick = this.tick.bind(this);
    this.onVis = () => {
      if (document.hidden) {
        cancelAnimationFrame(this.raf);
        this.raf = 0;
      } else if (!this.raf) {
        this.last = 0;
        this.raf = requestAnimationFrame(this.tick);
      }
    };
    document.addEventListener("visibilitychange", this.onVis);
    this.raf = requestAnimationFrame(this.tick);
  }

  fail(e) {
    if (this.failed) return;
    this.failed = true;
    this.onError?.(e);
  }

  viewState(cam) {
    const [longitude, latitude] = fromMerc(cam.c);
    return { longitude, latitude, zoom: cam.zoom, pitch: Math.max(0, cam.pitch), bearing: cam.bearing, maxPitch: 85, minZoom: 0, maxZoom: 24 };
  }

  buildStatic() {
    const { D, data } = this;
    const m = data.meta;
    const [x0, y0, x1, y1] = data.surroundings.ground;
    const L = {};
    L.base = new D.SolidPolygonLayer({
      id: "ground",
      data: [[[x0, y0, 0], [x1, y0, 0], [x1, y1, 0], [x0, y1, 0]]],
      getPolygon: (d) => d,
      getFillColor: RGB.ground,
      parameters: FLAT,
    });
    L.water = new D.SolidPolygonLayer({ id: "water", data: data.water, getPolygon: (d) => d, positionFormat: "XYZ", getFillColor: RGB.water, parameters: FLAT });
    const roads = (id, list) =>
      new D.PathLayer({
        id,
        data: list,
        getPath: (d) => d.p,
        positionFormat: "XYZ",
        getWidth: (d) => RGB.roadWidths[d.k],
        widthUnits: "meters",
        widthMinPixels: 0.6,
        getColor: (d) => RGB.roads[d.k],
        parameters: FLAT,
      });
    L.farRoads = roads("far-roads", data.surroundings.roads);
    L.roads = roads("roads", data.roads);
    L.shadowsCore = this.shadowLayer("shadows-core", data.shadows);
    L.ghosts = new D.PathLayer({
      id: "ghosts",
      data: this.vans.map((v) => {
        const end = v.ts[0] + v.loop;
        const pts = v.path.filter((_, i) => v.ts[i] <= end);
        return { p: flatPath(pts, 0.8), v2: v.id === 2 };
      }),
      getPath: (d) => d.p,
      positionFormat: "XYZ",
      getColor: (d) => (d.v2 ? [...ACC, 130] : [...RGB.trail, 56]),
      getWidth: (d) => (d.v2 ? 6 : 4),
      widthUnits: "meters",
      widthMinPixels: 1.1,
      widthMaxPixels: 6,
      jointRounded: true,
      parameters: FLAT,
    });
    L.stops = new D.ScatterplotLayer({
      id: "stops",
      data: this.vans.flatMap((v) => v.stops.map((p) => ({ p: [p[0], p[1], 1.0], v2: v.id === 2 }))),
      getPosition: (d) => d.p,
      getRadius: 3,
      radiusUnits: "pixels",
      stroked: true,
      getLineWidth: 1.5,
      lineWidthUnits: "pixels",
      getFillColor: RGB.building,
      getLineColor: (d) => (d.v2 ? ACC : RGB.ink),
      billboard: true,
      parameters: FLAT,
    });
    const st = m.street;
    const back = vanAt({ ...this.van2 }, m.passTime + 0.03);
    L.detour = new D.PathLayer({
      id: "detour",
      data: [{ p: flatPath([st, m.building.door, back], 1.1) }],
      getPath: (d) => d.p,
      positionFormat: "XYZ",
      getColor: ACC,
      getWidth: 3,
      widthUnits: "pixels",
      capRounded: true,
      jointRounded: true,
      parameters: FLAT,
    });
    L.door = new D.ScatterplotLayer({
      id: "door",
      data: [[...m.building.door, 1.2]],
      getPosition: (d) => d,
      getRadius: 4.5,
      radiusUnits: "pixels",
      stroked: true,
      getLineWidth: 1.5,
      lineWidthUnits: "pixels",
      getFillColor: ACC,
      getLineColor: RGB.ink,
      billboard: true,
      parameters: FLAT,
    });
    L.bCore = this.buildingLayer("buildings-core", data.buildings);
    const trail = (id, vans, color, w, min, max) =>
      new D.TripsLayer({
        id,
        data: vans.map((v) => ({ p: flatPath(v.path, 1.3), ts: v.ts })),
        getPath: (d) => d.p,
        positionFormat: "XYZ",
        getTimestamps: (d) => d.ts,
        getColor: color,
        getWidth: w,
        widthUnits: "meters",
        widthMinPixels: min,
        widthMaxPixels: max,
        trailLength: 22,
        fadeTrail: true,
        capRounded: true,
        jointRounded: true,
        currentTime: 30,
      });
    L.trailsOthers = trail("trails-others", this.vans.filter((v) => v.id !== 2), RGB.trail, 6, 2.2, 6);
    L.trailsVan2 = trail("trails-van2", [this.van2], ACC, 9, 4, 8);
    L.places = new D.TextLayer({
      id: "places",
      data: m.places,
      getPosition: (d) => [d.lon, d.lat, d.z],
      getText: (d) => d.text,
      getSize: 11,
      getColor: [...RGB.ink, 190],
      fontFamily: MONO,
      fontWeight: 600,
      fontSettings: { sdf: true, fontSize: 64, buffer: 8, radius: 12 },
      outlineWidth: 4,
      outlineColor: [...RGB.base, 255],
      parameters: ON_TOP,
    });
    this.buildTimeView(L);
    this.L = L;
  }

  buildTimeView(L) {
    const { D, data } = this;
    const door = data.meta.building.door;
    const street = data.meta.street;
    L.ribbons = new D.PathLayer({
      id: "tv-ribbons",
      data: this.vans.map(ribbon),
      getPath: (d) => d.p,
      positionFormat: "XYZ",
      getColor: (d) => (d.v2 ? ACC : [...RGB.ink, 170]),
      getWidth: (d) => (d.v2 ? 3.4 : 1.6),
      widthUnits: "pixels",
      capRounded: true,
      jointRounded: true,
    });
    const ring = (t) => Array.from({ length: 29 }, (_, i) => {
      const a = (i / 28) * Math.PI * 2;
      return [...offsetM(door, 38 * Math.cos(a), 38 * Math.sin(a)), TV_Z(t)];
    });
    const verticals = Array.from({ length: 6 }, (_, i) => {
      const a = (i / 6) * Math.PI * 2;
      const p = offsetM(door, 38 * Math.cos(a), 38 * Math.sin(a));
      return { path: [[...p, TV_Z(60)], [...p, TV_Z(180)]], c: [...ACC, 150], w: 1.1 };
    });
    L.column = new D.PathLayer({
      id: "tv-column",
      data: [
        { path: ring(60), c: [...ACC, 235], w: 1.6 },
        { path: ring(120), c: [...ACC, 110], w: 1.6 },
        { path: ring(180), c: [...ACC, 235], w: 1.6 },
        ...verticals,
      ],
      getPath: (d) => d.path,
      getColor: (d) => d.c,
      getWidth: (d) => d.w,
      widthUnits: "pixels",
    });
    L.passDot = new D.ScatterplotLayer({
      id: "tv-pass",
      data: [[...street, TV_Z(105)]],
      getPosition: (d) => d,
      getRadius: 6.5,
      radiusUnits: "pixels",
      stroked: true,
      getLineWidth: 2,
      lineWidthUnits: "pixels",
      getFillColor: ACC,
      getLineColor: RGB.ink,
      billboard: true,
      parameters: ON_TOP,
    });
    const label = (id, items, bg, size, anchor, offset) =>
      new D.TextLayer({
        id,
        data: items,
        getPosition: (d) => d.p,
        getText: (d) => d.t,
        getSize: size,
        getColor: RGB.ink,
        fontFamily: MONO,
        fontWeight: 600,
        getTextAnchor: anchor,
        getAlignmentBaseline: "center",
        getPixelOffset: offset,
        background: true,
        getBackgroundColor: bg,
        backgroundPadding: [6, 4],
        parameters: ON_TOP,
      });
    const pass = [{ p: [...street, TV_Z(105)], t: "VAN 2 PASSES 1:45 PM" }];
    L.passLabel = label("tv-pass-label", pass, ACC, 12, "end", [-20.5, 0]);
    // Phones: one pixel smaller so the label isn't cut by the left edge
    L.passLabelPhone = label("tv-pass-label-phone", pass, ACC, 11, "end", [-20.5, 0]);
    const east = offsetM(door, 58, 0);
    L.hours = label(
      "tv-hours",
      [60, 120, 180].map((t, i) => ({ p: [...east, TV_Z(t)], t: `${i + 1} PM` })),
      [...RGB.paper, 240],
      11,
      "start",
      [0, 0],
    );
  }

  shadowLayer(id, raw) {
    return new this.D.SolidPolygonLayer({ id, data: raw, getPolygon: (d) => d, positionFormat: "XYZ", getFillColor: RGB.shadow, parameters: FLAT });
  }

  buildingLayer(id, list) {
    return new this.D.SolidPolygonLayer({
      id,
      data: list,
      getPolygon: (d) => d.p,
      positionFormat: "XYZ",
      extruded: true,
      getElevation: (d) => d.h,
      getFillColor: RGB.building,
      material: MAT_B,
    });
  }

  addRest(bRaw, sRaw) {
    if (this.degraded || this.destroyed) return;
    const c = this.data.meta.coder;
    this.rest = { b: this.buildingLayer("buildings-rest", decodeBuildings(bRaw, c)), s: this.shadowLayer("shadows-rest", decodeShadows(sRaw, c)) };
  }

  beginIntro() {
    if (this.introAt == null) this.introAt = performance.now();
  }

  setReduced(r) {
    this.reduced = r;
  }

  measure(now, dt) {
    if (this.degraded || !dt) return;
    const it = this.introAt == null ? -1 : (now - this.introAt) / 1000;
    if (it < 3.2 && !this.reduced) return;
    const p = this.perf;
    if (!p.t0) p.t0 = now;
    p.sum += dt;
    p.n += 1;
    if (now - p.t0 >= 3000) {
      if (p.sum / p.n > 0.04) {
        this.degraded = true;
        this.rest = null;
        this.deck.setProps({ useDevicePixels: 1 });
      }
      p.sum = 0;
      p.n = 0;
      p.t0 = now;
    }
  }

  tick(now) {
    this.raf = requestAnimationFrame(this.tick);
    try {
      this.frame(now);
    } catch (e) {
      cancelAnimationFrame(this.raf);
      this.fail(e);
    }
  }

  frame(now) {
    if (window.__lpFreeze && this.frames > window.__lpFreeze) return;
    const dt = this.last ? Math.min(0.25, (now - this.last) / 1000) : 0;
    this.last = now;
    this.frames += 1;
    this.measure(now, dt);
    const W = this.canvas.clientWidth || window.innerWidth;
    const H = this.canvas.clientHeight || window.innerHeight;
    const P = this.getP();
    const red = this.reduced;
    const it = this.introAt == null ? -1 : (now - this.introAt) / 1000;
    const rise = red ? 1 : it < 0 ? 0.02 : 0.02 + 0.98 * easeOutCubic(clamp((it - 0.15) / 2.3));
    const shadowA = red ? 1 : clamp((it - 1.5) / 1.1);
    const trailA = red ? 1 : clamp((it - 1.3) / 0.6);
    if (P <= 0.24) {
      if (red) this.hero = 70;
      else if (it >= 1.4) {
        this.hero += dt * 5;
        if (this.hero > 80) this.hero = 30 + (this.hero - 80);
      }
    }
    const clock = storyClock(P, this.hero);
    const loopA = P <= 0.24 && !red ? clamp(Math.min(clock - 30, 80 - clock) / 0.65) : 1;
    const lift = liftAt(P);

    // Camera
    const scroll = this.cam.scroll(P, W, H, this.phone, red);
    let cam = scroll;
    if (!red) {
      const intro = this.cam.intro(W, H, this.phone);
      if (it < 0) cam = intro;
      else if (it < 2.9) cam = flight(intro, scroll, easeInOutCubic(it / 2.9));
      const s = now / 1000;
      cam = { ...cam, bearing: cam.bearing + 1.3 * Math.sin(0.26 * s), pitch: cam.pitch + 0.7 * Math.sin(0.24 * s) };
    }
    const viewState = { ...this.viewState(cam), ...(window.__lpCam || {}) };
    const zoom = viewState.zoom;
    const restOn = Boolean(this.rest) && it >= 3.3;
    const layers = this.layers({ P, clock, lift, rise, shadowA, trailA: trailA * loopA, zoom, restOn });
    const keep = window.__lpOnly;
    this.deck.setProps({ viewState, layers: keep ? layers.filter((l) => keep.some((k) => l.id.startsWith(k))) : layers });
    (this.times = this.times || []).push(Math.round(now));
    this.writeUI(now, { W, H, P, clock, viewState, rise });
  }

  layers({ P, clock, lift, rise, shadowA, trailA, zoom, restOn }) {
    const { L, D, data } = this;
    const m = data.meta;
    const ground = 1 - lift;
    const out = [L.base, L.water, L.farRoads, L.roads];
    if (!this.degraded) {
      out.push(L.shadowsCore.clone({ opacity: shadowA }));
      if (restOn) out.push(this.rest.s.clone({ opacity: shadowA }));
    }
    out.push(L.ghosts, L.stops);
    const detA = ramp(4.3, 4.5, P);
    if (detA > 0) out.push(L.detour.clone({ opacity: detA }), L.door.clone({ opacity: detA }));
    out.push(L.bCore.clone({ elevationScale: rise }));
    if (restOn) out.push(this.rest.b.clone({ elevationScale: rise }));
    // Customer building: white -> accent between P 1.55 and 1.85
    const k = Math.round(ramp(1.55, 1.85, P) * 24) / 24;
    const col = RGB.building.map((c, i) => Math.round(c + (ACC[i] - c) * k));
    out.push(
      new D.SolidPolygonLayer({
        id: "customer",
        data: [m.building.ring],
        getPolygon: (d) => d,
        extruded: true,
        getElevation: m.building.h,
        getFillColor: col,
        material: MAT_B,
        elevationScale: rise,
        updateTriggers: { getFillColor: k },
      }),
    );
    const tA = trailA * ground;
    if (tA > 0.002) {
      out.push(L.trailsOthers.clone({ currentTime: clock, opacity: tA }), L.trailsVan2.clone({ currentTime: clock, opacity: tA }));
    }
    // Vans
    const vans = this.vans.map((v) => {
      const p = vanAt(v, clock);
      return { p, yaw: v.heading || 0, v2: v.id === 2 };
    });
    this.vanNow = vans;
    const meshA = ramp(14.9, 15.7, zoom);
    if ((1 - meshA) * ground > 0.002) {
      out.push(
        new D.ScatterplotLayer({
          id: "van-dots",
          data: vans,
          getPosition: (d) => [d.p[0], d.p[1], 1.6],
          getRadius: (d) => (d.v2 ? 6 : 4.5),
          radiusUnits: "pixels",
          stroked: true,
          getLineWidth: 2,
          lineWidthUnits: "pixels",
          getFillColor: (d) => (d.v2 ? ACC : RGB.van),
          getLineColor: RGB.paper,
          billboard: true,
          opacity: (1 - meshA) * ground,
        }),
      );
    }
    if (meshA * ground > 0.002) {
      out.push(
        new D.SimpleMeshLayer({
          id: "van-mesh",
          data: vans,
          mesh: this.mesh,
          getPosition: (d) => [d.p[0], d.p[1], 0],
          getOrientation: (d) => [0, d.yaw, 0],
          getColor: (d) => (d.v2 ? ACC : RGB.van),
          sizeScale: clamp(Math.pow(2, 18.2 - zoom), 2.4, 10),
          material: MAT_V,
          opacity: meshA * ground,
        }),
      );
    }
    // Customer pin
    const pinA = ramp(1.55, 1.8, P);
    const c = m.building.center;
    const roof = m.building.h * rise;
    const mpp = (40075016.686 * Math.cos((c[1] * Math.PI) / 180)) / (512 * Math.pow(2, zoom));
    this.pinTop = [c[0], c[1], roof + 66 * mpp];
    if (pinA > 0) {
      out.push(
        new D.LineLayer({
          id: "pin-line",
          data: [0],
          getSourcePosition: () => [c[0], c[1], roof],
          getTargetPosition: () => this.pinTop,
          getColor: RGB.ink,
          getWidth: 1.5,
          widthUnits: "pixels",
          opacity: pinA,
          parameters: ON_TOP,
        }),
        new D.ScatterplotLayer({
          id: "pin-dot",
          data: [0],
          getPosition: () => this.pinTop,
          getRadius: 6,
          radiusUnits: "pixels",
          stroked: true,
          getLineWidth: 2,
          lineWidthUnits: "pixels",
          getFillColor: ACC,
          getLineColor: RGB.ink,
          billboard: true,
          opacity: pinA,
          parameters: ON_TOP,
        }),
      );
    }
    if (lift > 0) out.push(...this.timeView(lift, clock, vans));
    const placeA = (1 - ramp(13.0, 14.2, zoom)) * (1 - clamp(lift * 2));
    if (placeA > 0.002) out.push(L.places.clone({ opacity: placeA }));
    return out;
  }

  timeView(lift, clock, vans) {
    const { L, D } = this;
    const M = zMatrix(lift);
    const a = Math.min(1, 1.4 * lift);
    const labA = ramp(0.55, 0.8, lift);
    const out = [L.ribbons.clone({ modelMatrix: M, opacity: a }), L.column.clone({ modelMatrix: M, opacity: a }), L.passDot.clone({ modelMatrix: M, opacity: a })];
    out.push(
      new D.ScatterplotLayer({
        id: "tv-now",
        data: vans,
        getPosition: (d) => [d.p[0], d.p[1], TV_Z(clock) * lift],
        getRadius: 4,
        radiusUnits: "pixels",
        stroked: true,
        getLineWidth: 1.5,
        lineWidthUnits: "pixels",
        getFillColor: (d) => (d.v2 ? ACC : RGB.van),
        getLineColor: RGB.paper,
        billboard: true,
        opacity: a,
        parameters: ON_TOP,
      }),
    );
    const passLabel = this.phone ? L.passLabelPhone : L.passLabel;
    if (labA > 0) out.push(passLabel.clone({ modelMatrix: M, opacity: labA }), L.hours.clone({ modelMatrix: M, opacity: labA }));
    return out;
  }

  // HTML outside the canvas: clock, marker, band, request tag, offer sign. Up to 30 times a second.
  writeUI(now, { W, H, P, clock, viewState }) {
    if (now - this.lastUI < 33) return;
    this.lastUI = now;
    const ui = this.ui;
    const txt = fmtClock(clock);
    if (ui.clock && ui.clock.textContent !== txt) ui.clock.textContent = txt;
    const left = `${rulerPct(clock).toFixed(2)}%`;
    if (ui.marker && ui.marker.style.left !== left) ui.marker.style.left = left;
    const band = String(ramp(1.6, 1.9, P).toFixed(2));
    if (ui.band && ui.band.style.opacity !== band) ui.band.style.opacity = band;
    const tagA = ramp(1.72, 1.9, P) * (1 - ramp(2.42, 2.6, P));
    const signOn = P >= 4.28 && P < 5.06;
    if (signOn !== this.signOn) {
      this.signOn = signOn;
      this.onSign?.(signOn);
    }
    if (tagA <= 0 && !signOn) {
      if (ui.tag && ui.tag.style.opacity !== "0") ui.tag.style.opacity = "0";
      return;
    }
    const vp = new this.D.WebMercatorViewport({ ...viewState, width: W, height: H });
    const [x, y] = vp.project(this.pinTop);
    if (ui.tag) {
      const tx = clamp(x, 130, W - 130);
      const ty = clamp(y, 150, H - 90);
      const tr = `translate(${tx.toFixed(1)}px, ${ty.toFixed(1)}px)`;
      if (ui.tag.style.transform !== tr) ui.tag.style.transform = tr;
      const o = tagA.toFixed(2);
      if (ui.tag.style.opacity !== o) ui.tag.style.opacity = o;
    }
    if (ui.sign && !this.phone && signOn) {
      const sx = clamp(x, 40 + 22, W - 340 + 22);
      const sy = clamp(y, 340, H - 90);
      const tr = `translate(${sx.toFixed(1)}px, ${sy.toFixed(1)}px)`;
      if (ui.sign.style.transform !== tr) ui.sign.style.transform = tr;
    }
  }

  destroy() {
    this.destroyed = true;
    cancelAnimationFrame(this.raf);
    document.removeEventListener("visibilitychange", this.onVis);
    try {
      this.deck.finalize();
    } catch {
      /* ignore */
    }
  }
}
