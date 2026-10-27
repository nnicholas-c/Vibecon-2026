import { useId, useState } from "react";
import { AlertTriangle, ChevronDown } from "lucide-react";

const STATE = {
  not_started: ["Not started", "idle"], driving: ["On route", "live"], at_stop: ["At a stop", "live"],
  returning: ["Heading back", "live"], back: ["Back at base", "idle"], depot: ["No route today", "idle"],
};

const pt = (r, deg) => [50 + r * Math.cos((deg * Math.PI) / 180), 50 + r * Math.sin((deg * Math.PI) / 180)];
const SEGS = Array.from({ length: 54 }, (_, i) => {
  const [x0, y0] = pt(40, i * 5);
  const [x1, y1] = pt(40, Math.min(i * 5 + 5.6, 270));
  return { d: `M${x0.toFixed(2)} ${y0.toFixed(2)}A40 40 0 0 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`, c: "#FF5B1F" };
});
const TICKS = Array.from({ length: 28 }, (_, i) => {
  const major = i % 9 === 0;
  const [x0, y0] = pt(major ? 25.5 : 28, i * 10);
  const [x1, y1] = pt(32, i * 10);
  return { x0, y0, x1, y1, major };
});

function DayDial({ used, shift }) {
  const ratio = shift ? Math.min(used / shift, 1) : 0;
  const arc = 0.75;
  const mid = useId().replace(/:/g, "");
  return (
    <div className="dp-gauge" data-testid="gauge-day-used">
      <div className="relative h-[84px] w-[84px]">
        <span className="dp-dial-face" aria-hidden="true" />
        <svg viewBox="0 0 100 100" className="relative h-[84px] w-[84px]" aria-hidden="true">
          <defs>
            <mask id={`m${mid}`} maskUnits="userSpaceOnUse" x="0" y="0" width="100" height="100">
              <circle cx="50" cy="50" r="40" pathLength="1" className="dp-dial-fill" strokeDasharray={`${arc * ratio} 1`} style={{ "--dial": arc * ratio, stroke: "#fff" }} />
            </mask>
          </defs>
          <circle cx="50" cy="50" r="40" pathLength="1" className="dp-dial-track" strokeDasharray={`${arc} 1`} />
          {TICKS.map((t, i) => <line key={i} x1={t.x0} y1={t.y0} x2={t.x1} y2={t.y1} className={t.major ? "dp-tick is-major" : "dp-tick"} />)}
          <g mask={`url(#m${mid})`}>
            {SEGS.map((s, i) => <path key={i} d={s.d} stroke={s.c} className="dp-dial-seg" />)}
          </g>
        </svg>
      </div>
      <p className="tnum -mt-[58px] text-center font-display text-xl font-semibold" data-testid="gauge-day-used-value">{Math.round(ratio * 100)}%</p>
      <p className="mt-6 text-center text-[11px] text-[var(--dp-ink-2)]" data-testid="gauge-day-used-label">Driving and stops: {Math.round(used)} of {shift} min</p>
    </div>
  );
}

function SpareFill({ spare, shift }) {
  const ratio = shift ? Math.min(spare / shift, 1) : 0;
  return (
    <div className="dp-gauge dp-fill-tile" data-testid="gauge-spare">
      <div className="dp-fill" style={{ height: `${Math.max(ratio * 100, 8)}%` }} aria-hidden="true"><span className="dp-wave" /></div>
      <span className="dp-fill-ticks" aria-hidden="true" />
      <div className="relative">
        <p className="tnum font-display text-2xl font-semibold" data-testid="gauge-spare-value">{spare}</p>
        <p className="text-[11px] text-[var(--dp-ink-2)]">Spare minutes</p>
        <p className="tnum text-[11px] text-[var(--dp-ink-3)]">{Math.round(ratio * 100)}% of the shift</p>
      </div>
    </div>
  );
}

const isPhone = () => Boolean(window.matchMedia?.("(max-width: 767px)").matches);

export function VanDetailCard({ unit, plan, timeline, position, insight, clock, clockLabel }) {
  const [label, tone] = STATE[position?.state] || STATE.depot;
  const total = timeline.length;
  const idx = position?.next_index ?? 0;
  const next = timeline[idx];
  const start = plan?.start_departure ?? 0;
  const end = plan?.return_time ?? 1;
  const progress = Math.max(0, Math.min(1, (clock - start) / Math.max(end - start, 1)));
  const [phone] = useState(isPhone);
  const [open, setOpen] = useState(() => !isPhone());
  const collapsed = phone && !open;
  const stopText = idx >= total ? `All ${total} stops done` : `Stop ${idx + 1} of ${total}`;
  const head = (
    <span className="flex min-w-0 items-center gap-2">
      <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: unit.color }} />
      <span className={`font-display font-semibold ${collapsed ? "text-base" : "text-lg"}`} data-testid="van-detail-name">{unit.name}</span>
    </span>
  );
  const status = <span className={`dp-status shrink-0 ${tone === "live" ? "is-live" : ""}`} data-testid="van-detail-status">{label}</span>;
  const top = collapsed ? (
    <>
      {head}
      {status}
      <span className="tnum ml-auto truncate text-[11px] text-[var(--dp-ink-2)]" data-testid="van-detail-collapsed-summary">
        <span data-testid="van-detail-stop-count">{stopText}</span> · <b className="font-semibold text-[var(--dp-ink)]" data-testid="van-detail-collapsed-spare">{unit.spare_minutes}</b> spare
      </span>
    </>
  ) : <>{head}{status}</>;
  return (
    <div className={`dp-detail-card${collapsed ? " is-collapsed" : ""}`} data-testid="van-detail-card" data-collapsed={collapsed ? "true" : "false"}>
      {phone ? (
        <button type="button" onClick={() => setOpen((v) => !v)} aria-expanded={!collapsed} aria-label={collapsed ? "Show van details" : "Hide van details"}
          className="flex w-full items-center gap-2 text-left" data-testid="van-detail-toggle">
          {top}
          <ChevronDown className={`h-4 w-4 shrink-0 text-[var(--dp-ink-2)] transition-transform ${collapsed ? "" : "ml-auto rotate-180"}`} />
        </button>
      ) : (
        <div className="flex items-center justify-between gap-2">{top}</div>
      )}
      {!collapsed && (
      <div data-testid="van-detail-body">
      <p className="tnum mt-3 text-xs text-[var(--dp-ink-3)]" data-testid="van-detail-stop-count">
        {stopText}
      </p>
      {next && (
        <p className="mt-0.5 truncate text-sm" data-testid="van-detail-next-stop">
          {position?.state === "at_stop" ? "Now at" : "Next"} <b className="font-semibold">{next.customer_name}</b>
          <span className="tnum text-[var(--dp-ink-2)]"> · {next.arrival_label}</span>
        </p>
      )}
      <div className="mt-3">
        <div className="dp-stripe-track" data-testid="van-detail-progress" data-progress={progress.toFixed(3)}>
          <span className="dp-stripe" style={{ width: `${progress * 100}%` }} />
        </div>
        <div className="tnum mt-1.5 flex justify-between text-[11px] text-[var(--dp-ink-3)]">
          <span>{plan?.start_label} start</span>
          <span>{clockLabel} now</span>
          <span data-testid="van-detail-return">Back {plan?.return_label}</span>
        </div>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <DayDial used={unit.busy_minutes} shift={unit.shift_minutes} />
        <SpareFill spare={unit.spare_minutes} shift={unit.shift_minutes} />
      </div>
      {insight && (
        <div className="dp-insight" data-testid="van-insight-banner" role="status">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{insight.text}</span>
        </div>
      )}
      </div>
      )}
    </div>
  );
}
