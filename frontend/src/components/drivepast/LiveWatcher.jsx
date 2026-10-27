import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useFleet } from "@/context/FleetContext";
import { http } from "@/lib/api";
import { PriceRuler } from "./PriceRuler";
import { inDemoSession, onFleet } from "./DemoAutoplay";

const LIVE_MS = 5000;
const DEMO_LIVE_MS = 2500;
const EVENTS_MS = 10000;

// One toast per booking, from whichever poll sees it first (/api/live every 5 s or /api/events every 10 s).
const toasted = new Set();

// Add .dp-flash to the matching elements for 3 s from when they first appear (map pins redraw after the reload).
function flashFor(selector) {
  const t0 = Date.now();
  let start = 0;
  const tick = () => {
    const els = document.querySelectorAll(selector);
    if (els.length && !start) start = Date.now();
    const on = start && Date.now() - start < 3000;
    els.forEach((el) => el.classList.toggle("dp-flash", Boolean(on)));
    if (on || (!start && Date.now() - t0 < 8000)) setTimeout(tick, 150);
  };
  tick();
}

export function bookingToast(text, ruler, unitKey, auto, navigate, extra = {}) {
  if (!text || toasted.has(text)) return;
  toasted.add(text);
  const demo = inDemoSession() && onFleet();
  toast.success(text, { duration: demo ? 30000 : 8000, position: "bottom-right", id: `booking-${text}`,
    description: (ruler || auto || extra.earn_line) ? (
      <div className="space-y-2">
        {ruler && <PriceRuler price={ruler.price} usual={ruler.usual} />}
        {extra.earn_line && <p className="text-xs font-semibold text-[var(--dp-ink)]" data-testid="booking-earn-line">{extra.earn_line}</p>}
        {auto && (
          <button type="button" onClick={() => navigate("/settings#auto-send")} className="text-xs font-semibold text-[var(--dp-ink)] underline" data-testid="booking-auto-sent-link">
            Auto-sent within your rules
          </button>
        )}
      </div>
    ) : undefined });
  if (unitKey) {
    flashFor(`[data-testid="dispatch-row-${unitKey}"]`);
    flashFor(`[data-testid^="map-marker-${unitKey}-"].is-new`);
  }
  window.dispatchEvent(new CustomEvent("dp-autoplay", { detail: { ...extra, unit_key: unitKey } }));
}

// REQ-1401/1402: in a demo session, show on Fleet that a new request is being read, and say why if it's held.
const arrivals = new Set();
function arrivalToast(r) {
  if (!r || !inDemoSession() || !onFleet()) return;
  if (!arrivals.has(r.key)) {
    arrivals.add(r.key);
    toast(`Reading a request from ${r.sender}.`, { id: `arrival-${r.key}`, duration: 6000, position: "bottom-right" });
  }
  if (r.held && !arrivals.has(`${r.key}-held`)) {
    arrivals.add(`${r.key}-held`);
    toast.warning(`Held: the request from ${r.sender}. ${r.reason || ""}`.trim(), { id: `held-${r.key}`, duration: 20000, position: "bottom-right" });
  }
}

// Polls /api/events?since=... every 10 s and shows each van reorder as a toast, with a map overlay.
export function ReorderToasts() {
  const { reload, setReorderFx } = useFleet();
  const navigate = useNavigate();
  useEffect(() => {
    let since = "";
    const tick = async () => {
      try {
        const { data } = await http.get("/events", { params: since ? { since } : {} });
        if (since && data.events.length) {
          data.events.filter((e) => e.kind === "booked").forEach((e) => bookingToast(e.text, e.ruler, e.van_id, true, navigate,
            { earn_line: e.earn_line, customer: e.customer, unit_name: e.unit_name, request_key: e.request_key }));
          data.events.filter((e) => e.kind !== "booked").forEach((e) => {
            const play = () => setReorderFx({ ...e, at: Date.now() });
            play();
            toast(e.text, { id: `reorder-${e.ts}`, duration: 9000,
              action: { label: "Show on map", onClick: () => { navigate(`/units/${e.van_id}`); play(); } } });
          });
          reload();
        }
        since = data.now;
      } catch { /* next tick retries */ }
    };
    tick();
    const t = setInterval(tick, EVENTS_MS);
    return () => clearInterval(t);
  }, [reload, setReorderFx, navigate]);
  return null;
}

// Polls the owner-screen live state (booking toasts, inbox badge) every 5 s while the tab is visible. Sheets sync on the backend.
export function LiveWatcher() {
  const { fleet, reload, setHighlight, setLive } = useFleet();
  const navigate = useNavigate();
  const seen = useRef(undefined);
  const sig = useRef("");
  const count = useRef(fleet?.inbox_new_count);
  count.current = fleet?.inbox_new_count;

  useEffect(() => {
    let dead = false;
    const tick = async () => {
      try {
        const { data } = await http.get("/live");
        if (dead) return;
        setLive(data);
        const b = data.last_booking;
        if (seen.current !== undefined) arrivalToast(data.latest_request);
        else if (data.latest_request) arrivals.add(data.latest_request.key).add(`${data.latest_request.key}-held`);
        if (seen.current !== undefined && b && b.id !== seen.current) {
          setHighlight(b.stop_keys, 60000);
          reload();
          bookingToast(b.toast, b.ruler, b.unit_key, b.auto, navigate,
            { earn_line: b.earn_line, customer: b.customer, unit_name: b.unit_name, request_key: b.request_key });
        } else if ((count.current !== undefined && data.inbox_new_count !== count.current) || (sig.current && data.routes_sig !== sig.current)) {
          reload();
        }
        sig.current = data.routes_sig;
        seen.current = b ? b.id : null;
      } catch { /* next tick retries */ }
    };
    let t = null;
    const sync = () => {
      clearInterval(t);
      t = null;
      if (document.visibilityState === "visible") {
        tick();
        t = setInterval(tick, inDemoSession() ? DEMO_LIVE_MS : LIVE_MS);
      }
    };
    sync();
    document.addEventListener("visibilitychange", sync);
    return () => { dead = true; clearInterval(t); document.removeEventListener("visibilitychange", sync); };
  }, [reload, setHighlight, setLive, navigate]);

  return null;
}
