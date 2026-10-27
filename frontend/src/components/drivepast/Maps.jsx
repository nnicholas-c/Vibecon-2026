import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { http } from "@/lib/api";
import { useFleet } from "@/context/FleetContext";
import { Switch } from "@/components/ui/switch";
import RouteMap from "./RouteMap";
import { SegPills } from "./SegPills";
import { useStreetLines } from "./streetLines";

export function unitRoute(unit, timeline, position, oldSeq) {
  return {
    unit_key: unit.key, name: unit.name, color: unit.color, position,
    start_location: unit.start_location, end_location: unit.end_location,
    stops: timeline.map((r) => ({
      key: r.stop_key, seq: r.seq, lat: r.lat, lon: r.lon, name: r.customer_name, address: r.address,
      arrival_label: r.arrival_label, window_label: r.window_label, is_new: r.source === "quote",
      old_seq: oldSeq?.[r.stop_key],
    })),
  };
}

const FX_MS = 6000;

// The step 8 reorder event replayed on this van's map: old order dashed and faint, new order in the van's color.
function useReorderFx(unit, timeline) {
  const { reorderFx } = useFleet();
  const [on, setOn] = useState(false);
  const fx = reorderFx && reorderFx.van_id === unit.key ? reorderFx : null;
  useEffect(() => {
    if (!fx) return undefined;
    const left = fx.at + FX_MS - Date.now();
    if (left <= 0) return undefined;
    setOn(true);
    const t = setTimeout(() => setOn(false), left);
    return () => clearTimeout(t);
  }, [fx?.at, fx?.ts]);
  return useMemo(() => {
    if (!on || !fx?.old_order) return null;
    const pts = Object.fromEntries(timeline.map((r) => [r.stop_key, [r.lat, r.lon]]));
    const old = fx.old_order.filter((k) => pts[k]);
    const ends = (loc) => [loc.lat, loc.lon];
    return {
      key: fx.ts,
      path: [ends(unit.start_location), ...old.map((k) => pts[k]), ends(unit.end_location)],
      oldSeq: Object.fromEntries(old.map((k, i) => [k, i + 1])),
    };
  }, [on, fx, timeline, unit]);
}

function proposalPaths(route, opt) {
  const pts = Object.fromEntries(route.stops.map((s) => [s.key, [s.lat, s.lon]]));
  opt.new_stops.forEach((s) => { pts[s.key] = [s.lat, s.lon]; });
  const start = [route.start_location.lat, route.start_location.lon];
  const end = [route.end_location.lat, route.end_location.lon];
  const seq = opt.sequence.filter((k) => pts[k]);
  const paths = [];
  for (let i = 0; i < seq.length; i += 1) {
    if (!seq[i].startsWith("new:")) continue;
    let j = i;
    while (j < seq.length && seq[j].startsWith("new:")) j += 1;
    paths.push([i > 0 ? pts[seq[i - 1]] : start, ...seq.slice(i, j).map((k) => pts[k]), j < seq.length ? pts[seq[j]] : end]);
    i = j;
  }
  return paths;
}

const CARD_PAD = { paddingTopLeft: [340, 36], paddingBottomRight: [72, 36] };
const scrollTo = (id) => document.querySelector(`[data-testid="${id}"]`)?.scrollIntoView({ behavior: "smooth", block: "start" });

export function UnitMap({ unit, timeline, previewId, position, children }) {
  const navigate = useNavigate();
  const [opt, setOpt] = useState(null);
  const [previewError, setPreviewError] = useState("");
  const fx = useReorderFx(unit, timeline);
  const route = useMemo(() => unitRoute(unit, timeline, position, fx?.oldSeq), [unit, timeline, position, fx]);

  useEffect(() => {
    setOpt(null);
    setPreviewError("");
    if (!previewId) return;
    http.get(`/engine/options/${previewId}`)
      .then(({ data }) => (data.unit_key === unit.key ? setOpt(data) : setPreviewError("That proposal belongs to another van.")))
      .catch(() => setPreviewError("That proposal isn't available anymore. Price it again."));
  }, [previewId, unit.key]);

  const baseRoutes = useMemo(() => [route], [route]);
  const { routes, note } = useStreetLines(baseRoutes);
  const proposal = useMemo(() => (opt ? { color: "#FF5B1F", stops: opt.new_stops, paths: proposalPaths(route, opt) } : null), [opt, route]);

  return (
    <div className="space-y-3" data-testid="unit-map-section">
      {(opt || previewError) && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-[var(--dp-card)] px-4 py-3 text-sm" data-testid="map-preview-banner">
          <span>{previewError || "Showing the proposed new stops (dashed line). Nothing is booked."}</span>
          <button className="font-semibold underline underline-offset-4" onClick={() => navigate(`/units/${unit.key}`)} data-testid="map-preview-clear">Clear</button>
        </div>
      )}
      {fx && (
        <div className="flex flex-wrap items-center gap-4 border border-[var(--dp-ink)] bg-[var(--dp-surface)] px-4 py-2 font-mono text-xs uppercase tracking-wider" data-testid="map-reorder-legend">
          <span className="flex items-center gap-2"><span className="inline-block w-8 border-t-2 border-dashed border-[var(--dp-ink-3)]" />Old order</span>
          <span className="flex items-center gap-2"><span className="inline-block h-[3px] w-8" style={{ background: unit.color }} />New order</span>
          <span className="text-[var(--dp-ink-3)]">Pins show old → new stop number</span>
        </div>
      )}
      <RouteMap routes={routes} proposal={proposal} ghost={fx} testId="unit-map" selectedKey={fx ? undefined : unit.key} follow className="h-[62vh] min-h-[540px]"
        fitPadding={CARD_PAD} onList={() => scrollTo("unit-timeline-card")} lineNote={note}>
        {children}
      </RouteMap>
    </div>
  );
}

function fleetGroups(units, stats) {
  const rate = Object.fromEntries((stats || []).map((u) => [u.key, u.on_time_rate]));
  const max = Math.max(...units.map((u) => u.spare_minutes ?? 0));
  const keys = (fn) => new Set(units.filter(fn).map((u) => u.unit_key));
  return {
    all: keys(() => true),
    spare: keys((u) => (u.spare_minutes ?? 0) >= max - 10),
    late: keys((u) => rate[u.unit_key] != null && rate[u.unit_key] < 95),
    fresh: keys((u) => u.stops.some((s) => s.is_new)),
  };
}

const FILTERS = [["all", "All"], ["spare", "Most spare"], ["late", "Late risk"], ["fresh", "New stops"]];

function Toggle({ label, checked, onChange, testId }) {
  return (
    <label className="flex cursor-pointer items-center gap-2 text-sm text-[var(--dp-ink-2)]">
      <Switch checked={checked} onCheckedChange={onChange} className="dp-switch" data-testid={testId} />
      {label}
    </label>
  );
}

export function FleetMap() {
  const navigate = useNavigate();
  const { fleet, version } = useFleet();
  const [units, setUnits] = useState(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [sel, setSel] = useState(null);
  const [showRoutes, setShowRoutes] = useState(true);
  const [showVans, setShowVans] = useState(true);
  useEffect(() => {
    http.get("/map/fleet").then(({ data }) => setUnits(data.units)).catch(() => setError("The fleet map didn't load. Try again in a moment."));
  }, [version]);
  const groups = useMemo(() => (units ? fleetGroups(units, fleet?.units) : null), [units, fleet]);
  const { routes: lined, note } = useStreetLines(units);
  const shown = useMemo(() => (units && groups ? lined.filter((u) => groups[filter].has(u.unit_key)) : []), [units, lined, groups, filter]);
  if (error) return <p className="text-sm text-[var(--dp-amber)]" data-testid="fleet-map-error">{error}</p>;
  if (!units) return <div className="dp-map h-[62vh] min-h-[420px]" data-testid="fleet-map-loading" />;
  const picked = units.find((u) => u.unit_key === sel);
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SegPills testId="fleet-filter" value={filter} onChange={(k) => { setFilter(k); setSel(null); }}
          options={FILTERS.map(([key, label]) => ({ key, label, count: groups[key].size }))} />
        <div className="flex items-center gap-4">
          <Toggle label="Show routes" checked={showRoutes} onChange={setShowRoutes} testId="fleet-toggle-routes" />
          <Toggle label="Show van icons" checked={showVans} onChange={setShowVans} testId="fleet-toggle-vans" />
        </div>
      </div>
      <RouteMap routes={shown} testId="dispatch-fleet-map" className="h-[62vh] min-h-[420px]" selectedKey={sel}
        showRoutes={showRoutes} showVans={showVans} onSelectVan={(k) => setSel((c) => (c === k ? null : k))} onList={() => scrollTo("dispatch-units-table")} lineNote={note}>
        {picked && (
          <div className="dp-detail-card !w-auto !max-w-[280px]" data-testid="fleet-selected-card">
            <div className="flex items-center justify-between gap-3">
              <span className="font-display text-base font-semibold">{picked.name}</span>
              <span className="dp-status is-live">Selected</span>
            </div>
            <p className="tnum mt-1 text-xs text-[var(--dp-ink-2)]">{picked.nickname} · {picked.stops.length} stops · {picked.spare_minutes} spare min</p>
            <button type="button" onClick={() => navigate(`/units/${picked.unit_key}`)} className="mt-3 text-sm font-semibold text-[var(--dp-ink)] underline underline-offset-4" data-testid="fleet-selected-open">
              Open {picked.name}
            </button>
          </div>
        )}
      </RouteMap>
      <div className="flex flex-wrap gap-2" data-testid="map-legend">
        {units.map((u) => (
          <button key={u.unit_key} onClick={() => navigate(`/units/${u.unit_key}`)} onMouseEnter={() => setSel(u.unit_key)} onFocus={() => setSel(u.unit_key)} data-testid={`map-legend-item-${u.unit_key}`}
            className={`dp-lift flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-[var(--dp-bg)] ${sel === u.unit_key ? "bg-[var(--dp-surface)] ring-1 ring-[var(--dp-accent)]" : "bg-[var(--dp-card)]"}`}>
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: u.color }} />
            {u.name}
            <span className="font-normal text-[var(--dp-ink-2)]">{u.nickname}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
