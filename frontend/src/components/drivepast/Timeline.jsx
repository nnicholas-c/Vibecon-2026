import { Fragment, useEffect, useState } from "react";
import { Check } from "lucide-react";
import { useFleet } from "@/context/FleetContext";

// "+N min" / "−N min" after a Done; hides itself after 60 s.
function ShiftTag({ minutes, testId }) {
  const [on, setOn] = useState(true);
  useEffect(() => {
    setOn(true);
    const t = setTimeout(() => setOn(false), 60000);
    return () => clearTimeout(t);
  }, [minutes]);
  if (!on) return null;
  return (
    <span className="border border-[var(--dp-ink)] bg-[var(--dp-accent)] px-1.5 py-0.5 font-mono text-[11px] font-semibold text-[var(--dp-ink)]" data-testid={testId}>
      {minutes > 0 ? "+" : "−"}{Math.abs(minutes)} min
    </span>
  );
}

function Marker({ color, hollow }) {
  return (
    <span
      className="relative z-10 mt-1.5 h-3 w-3 shrink-0 rounded-full border-2"
      style={{ borderColor: color, background: hollow ? "var(--dp-card)" : color }}
    />
  );
}

function EndRow({ time, label, color, testId }) {
  return (
    <li className="flex gap-4 py-2" data-testid={testId}>
      <span className="tnum w-16 shrink-0 pt-0.5 text-right text-sm font-semibold" data-testid={`${testId}-time`}>{time}</span>
      <Marker color={color} hollow />
      <span className="pt-0.5 text-sm text-[var(--dp-ink-2)]">{label}</span>
    </li>
  );
}

function NowRow({ label }) {
  return (
    <li className="flex items-center gap-4 py-1" data-testid="timeline-now-marker">
      <span className="tnum w-16 shrink-0 text-right text-xs font-semibold text-[var(--dp-green)]">{label}</span>
      <span className="h-px flex-1 bg-[var(--dp-green)]" />
      <span className="text-xs font-medium text-[var(--dp-green)]">Now</span>
    </li>
  );
}

function StopRow({ row, color }) {
  const i = row.seq;
  const { highlight } = useFleet();
  const lit = highlight.keys.includes(row.stop_key) && Date.now() < highlight.until;
  const done = (row.tags || []).includes("Done");
  return (
    <li className={`flex gap-4 py-2.5 ${done ? "opacity-45" : row.passed ? "opacity-60" : ""} ${lit ? "dp-new-stop" : ""}`} data-testid={`timeline-row-${i}`} data-new={lit ? "true" : undefined} data-done={done ? "true" : undefined}>
      <span className="tnum w-16 shrink-0 pt-0.5 text-right text-sm font-semibold" data-testid={`timeline-arrival-${i}`}>{row.arrival_label}</span>
      <Marker color={color} />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          {done && <Check className="h-4 w-4 text-[var(--dp-green)]" data-testid={`timeline-done-check-${i}`} />}
          <span className="font-medium" data-testid={`timeline-customer-${i}`}>{row.customer_name}</span>
          <span className="rounded-full bg-[var(--dp-bg)] px-2 py-0.5 text-[11px] text-[var(--dp-ink-2)]">
            {row.kind === "dropoff" ? "Drop-off" : row.kind === "job" ? "Job" : "Pickup"}
          </span>
          {row.passed && <span className="text-[11px] text-[var(--dp-ink-3)]">Done</span>}
          {(row.tags || []).map((t, ti) => (
            <span key={t} className="rounded-full bg-[var(--dp-green-soft)] px-2 py-0.5 text-[11px] font-medium text-[var(--dp-green)]" data-testid={`timeline-tag-${i}-${ti}`}>{t}</span>
          ))}
          {row.time_shift ? <ShiftTag minutes={row.time_shift} testId={`timeline-shift-${i}`} /> : null}
          {!row.in_window && <span className="rounded-full bg-[var(--dp-red-soft)] px-2 py-0.5 text-[11px] text-[var(--dp-red)]">Misses window</span>}
        </div>
        <p className="break-words text-sm text-[var(--dp-ink-2)]" data-testid={`timeline-address-${i}`}>{row.address}</p>
        <p className="tnum text-xs text-[var(--dp-ink-3)]">
          Window <span data-testid={`timeline-window-${i}`}>{row.window_label}</span>
          <span className="px-1.5">|</span>
          {Math.round(row.service_minutes_used * 10) / 10} min stop
        </p>
      </div>
    </li>
  );
}

export default function Timeline({ unit, plan, rows, clock, clockLabel }) {
  if (!plan) return <p className="text-sm text-[var(--dp-ink-2)]">This van has no route planned yet.</p>;
  const nowIndex = rows.findIndex((r) => r.arrival >= clock);
  const startName = unit.start_location?.name || "start";
  const endName = unit.end_location?.name || "end";
  return (
    <ol className="relative" data-testid="unit-timeline">
      <span className="absolute bottom-4 left-[85px] top-4 w-px bg-[var(--dp-line)]" aria-hidden />
      <EndRow time={plan.start_label} label={`Leaves the ${startName}`} color={unit.color} testId="timeline-start" />
      {rows.map((r, idx) => (
        <Fragment key={r.stop_key}>
          {idx === nowIndex && <NowRow label={clockLabel} />}
          <StopRow row={r} color={unit.color} />
        </Fragment>
      ))}
      {nowIndex === -1 && clock < plan.return_time && <NowRow label={clockLabel} />}
      <EndRow time={plan.return_label} label={`Back at the ${endName}`} color={unit.color} testId="timeline-return" />
    </ol>
  );
}
