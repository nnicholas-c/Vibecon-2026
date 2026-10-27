// Story math (PROMPT.md section 5): easing, the story clock, lift and chapters.
export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const ramp = (a, b, x) => clamp((x - a) / (b - a));
export const smooth = (a, b, x) => {
  const t = ramp(a, b, x);
  return t * t * (3 - 2 * t);
};
export const easeInOutCubic = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);
export const easeInOutSine = (t) => -(Math.cos(Math.PI * t) - 1) / 2;

// Ease-out that starts at the previous segment's speed and stops dead (Van 2 brakes into the door).
const brake = (t, m0) => (t * t * t - 2 * t * t + t) * m0 + (-2 * t * t * t + 3 * t * t);

export function storyClock(P, hero) {
  if (P <= 0.24) return hero;
  if (P <= 0.86) return hero + (82 - hero) * easeInOutCubic(ramp(0.24, 0.86, P));
  if (P <= 1.95) return 82 + 13 * ramp(0.86, 1.95, P);
  if (P <= 2.95) return 95 + 4 * ramp(1.95, 2.95, P);
  if (P <= 3.95) return 99 + 2.5 * ramp(2.95, 3.95, P);
  if (P <= 4.35) return 101.5 + 3.5 * brake(ramp(3.95, 4.35, P), (2.5 * 0.4) / 3.5);
  if (P <= 4.85) return 105;
  return 105 + 12 * ramp(4.85, 5.6, P);
}

export const liftAt = (P) => smooth(2.32, 2.9, P) * (1 - smooth(3.3, 3.78, P));

export const chapterAt = (P) => (P < 0.5 ? 0 : P < 1.5 ? 1 : P < 2.5 ? 2 : P < 3.5 ? 3 : P < 5.2 ? 4 : 5);

export function fmtClock(m) {
  const tot = Math.floor(m + 1e-6);
  const h24 = 12 + Math.floor(tot / 60);
  const mm = ((tot % 60) + 60) % 60;
  const h12 = ((h24 + 11) % 12) + 1;
  const ap = h24 % 24 >= 12 ? "PM" : "AM";
  return `${h12}:${String(mm).padStart(2, "0")} ${ap}`;
}

// Ruler runs from 12:00 (0) to 3:30pm (210)
export const rulerPct = (m) => (clamp(m, 0, 210) / 210) * 100;
