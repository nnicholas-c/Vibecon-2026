// Playing by itself (PROMPT.md 5.7): scrolls the window along a fixed script.
import { easeInOutCubic, easeInOutSine } from "./story";

const SCRIPT = [
  { hold: 1.6 },
  { to: 1, d: 2.8 },
  { hold: 1.6 },
  { to: 2, d: 2.8 },
  { hold: 1.8 },
  { to: 3, d: 3.9 },
  { hold: 2.9 },
  { to: 4.0, d: 3.6 },
  { hold: 0.1 },
  { to: 4.62, d: 3.6, ease: easeInOutSine },
  { hold: 2.0 },
  { to: 5.6, d: 3.0 },
];

export const fullScript = () => SCRIPT.map((s) => ({ ...s }));

// From the current spot: finish the move that's under way, then the rest.
export function scriptFrom(P) {
  let prevTo = 0;
  for (let i = 0; i < SCRIPT.length; i++) {
    const s = SCRIPT[i];
    if (s.to === undefined) continue;
    if (s.to > P + 0.01) {
      const frac = Math.min(1, (s.to - P) / Math.max(0.01, s.to - prevTo));
      return [{ ...s, d: Math.max(0.9, s.d * frac) }, ...SCRIPT.slice(i + 1).map((x) => ({ ...x }))];
    }
    prevTo = s.to;
  }
  return null;
}

export class Player {
  constructor({ getUnit, getP, onState }) {
    this.getUnit = getUnit;
    this.getP = getP;
    this.onState = onState;
    this.raf = 0;
    this.timer = 0;
    this.mode = "idle";
  }

  set(mode) {
    if (this.mode === mode) return;
    this.mode = mode;
    this.onState(mode);
  }

  run(steps, delay = 0) {
    this.stop();
    this.set("playing");
    this.timer = setTimeout(() => this.go(steps), delay * 1000);
  }

  // kind: "glide" doesn't count as playing for the masthead button
  go(steps, kind = "playing") {
    let from = this.getP();
    const plan = steps.map((s) => {
      const st = { ...s, from, to: s.to === undefined ? from : s.to, d: s.hold ?? s.d, ease: s.ease || easeInOutCubic };
      from = st.to;
      return st;
    });
    let i = 0;
    let t0 = performance.now();
    const tick = (now) => {
      while (i < plan.length && now - t0 >= plan[i].d * 1000) {
        t0 += plan[i].d * 1000;
        i += 1;
      }
      if (i >= plan.length) {
        const last = plan[plan.length - 1];
        if (last) window.scrollTo(0, last.to * this.getUnit());
        this.raf = 0;
        this.set("idle");
        return;
      }
      const s = plan[i];
      if (s.hold === undefined) {
        const u = Math.min(1, (now - t0) / (s.d * 1000));
        window.scrollTo(0, (s.from + (s.to - s.from) * s.ease(u)) * this.getUnit());
      }
      this.raf = requestAnimationFrame(tick);
    };
    if (kind !== "playing") this.set(kind);
    this.raf = requestAnimationFrame(tick);
  }

  glide(to) {
    this.stop();
    const d = 0.9 + 0.55 * Math.abs(to - this.getP());
    this.go([{ to, d }], "gliding");
  }

  stop() {
    clearTimeout(this.timer);
    if (this.raf) cancelAnimationFrame(this.raf);
    this.raf = 0;
    this.set("idle");
  }
}
