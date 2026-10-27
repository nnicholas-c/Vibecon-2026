// Camera keyframes and flights (PROMPT.md 5.2, 5.3).
import { MODEL_CENTER } from "./constants";
import { clamp, easeInOutCubic } from "./story";

const PI = Math.PI;
export const toMerc = ([lon, lat]) => [((lon + 180) / 360) * 512, ((PI - Math.log(Math.tan(PI / 4 + (lat * PI) / 360))) / (2 * PI)) * 512];
export const fromMerc = ([x, y]) => [(x / 512) * 360 - 180, ((2 * Math.atan(Math.exp(PI - (y / 512) * 2 * PI)) - PI / 2) * 180) / PI];

// s: subject. Strings resolve from meta at runtime.
export const KEYS = [
  { a: 0, b: 0.3, s: [-122.288, 37.836], f: [0.64, 0.64], z: 12.9, p: 56, br: -78, orbit: 6, drift: 0.1, ph: [0.5, 0.72, 11.9, 54] },
  { a: 0.92, b: 1.3, s: [-122.276, 37.83], f: [0.62, 0.58], z: 13.1, p: 52, br: -62, orbit: 8, drift: 0.1, ph: [0.5, 0.42, 12.1, 50] },
  { a: 1.95, b: 2.3, s: "center", f: [0.4, 0.6], z: 16.2, p: 58, br: -28, orbit: 14, drift: 0.14, ph: [0.5, 0.38, 15.7, 56] },
  { a: 2.95, b: 3.3, s: "door", f: [0.6, 0.84], z: 14.5, p: 62, br: -10, orbit: 16, drift: 0, ph: [0.5, 0.58, 13.9, 60] },
  // Phone deviation: spec says 0.46, 0.5, 17.5; nudged so the building stays on screen and the docked sign clears the pin.
  { a: 3.95, b: 4.85, s: "street", f: [0.56, 0.7], z: 18.1, p: 66, br: -14, orbit: 10, drift: 0.1, ph: [0.4, 0.56, 17.3, 64] },
  { a: 5.5, b: 5.6, s: [-122.283, 37.834], f: [0.62, 0.55], z: 12.9, p: 46, br: -95, orbit: 2, drift: 0, ph: [0.5, 0.4, 11.9, 46] },
];

export function sizeOffset(W, H, phone) {
  return phone ? clamp(Math.log2(Math.min(W / 390, H / 844)), -1.2, 0.8) : clamp(Math.log2(Math.min(W / 1440, H / 900)), -1.2, 0.8);
}

export class Camera {
  constructor(WebMercatorViewport, subjects) {
    this.WMV = WebMercatorViewport;
    this.keys = KEYS.map((k) => ({ ...k, s: typeof k.s === "string" ? subjects[k.s] : k.s }));
  }

  // Keyframe k at hold progress u (0..1) -> {c (mercator), zoom, pitch, bearing}
  pose(k, u, W, H, phone) {
    const K = this.keys[k];
    const [fx, fy, z0, p] = phone ? K.ph : [K.f[0], K.f[1], K.z, K.p];
    const zoom = z0 + sizeOffset(W, H, phone) + K.drift * (u - 0.5);
    const bearing = K.br + K.orbit * (u - 0.5);
    const vp = new this.WMV({ width: W, height: H, longitude: K.s[0], latitude: K.s[1], zoom, pitch: p, bearing });
    const G = vp.unproject([fx * W, fy * H]);
    const sm = toMerc(K.s);
    const gm = toMerc(G);
    return { c: [2 * sm[0] - gm[0], 2 * sm[1] - gm[1]], zoom, pitch: p, bearing };
  }

  scroll(P, W, H, phone, reduced) {
    const ks = this.keys;
    if (reduced) return this.pose(chapterKey(P), 0.5, W, H, phone);
    for (let i = 0; i < ks.length; i++) {
      const k = ks[i];
      if (P <= k.b || i === ks.length - 1) {
        if (P >= k.a || i === 0) return this.pose(i, clamp((P - k.a) / (k.b - k.a)), W, H, phone);
        const prev = ks[i - 1];
        const e = easeInOutCubic(clamp((P - prev.b) / (k.a - prev.b)));
        return flight(this.pose(i - 1, 1, W, H, phone), this.pose(i, 0, W, H, phone), e);
      }
    }
    return this.pose(ks.length - 1, 1, W, H, phone);
  }

  intro(W, H, phone) {
    return { c: toMerc(MODEL_CENTER), zoom: phone ? 11.3 : 12.4 + sizeOffset(W, H, false), pitch: 0, bearing: -60 };
  }
}

// Reduced motion: cut to the current chapter's keyframe.
export function chapterKey(P) {
  const ks = KEYS;
  for (let i = 0; i < ks.length - 1; i++) if (P < (ks[i].b + ks[i + 1].a) / 2) return i;
  return ks.length - 1;
}

// One smooth move: zoom about the fixed point F so it isn't a pan followed by a zoom.
export function flight(A, B, e) {
  const dz = B.zoom - A.zoom;
  const zoom = A.zoom + dz * e;
  let c;
  if (Math.abs(dz) < 0.05) {
    c = [A.c[0] + (B.c[0] - A.c[0]) * e, A.c[1] + (B.c[1] - A.c[1]) * e];
  } else {
    const r = Math.pow(2, -dz);
    const F = [(B.c[0] - r * A.c[0]) / (1 - r), (B.c[1] - r * A.c[1]) / (1 - r)];
    const k = Math.pow(2, A.zoom - zoom);
    c = [F[0] + (A.c[0] - F[0]) * k, F[1] + (A.c[1] - F[1]) * k];
  }
  const db = ((((B.bearing - A.bearing) % 360) + 540) % 360) - 180;
  return { c, zoom, pitch: A.pitch + (B.pitch - A.pitch) * e, bearing: A.bearing + db * e };
}
