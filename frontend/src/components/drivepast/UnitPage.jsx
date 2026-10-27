import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Clock, MapPin } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useFleet } from "@/context/FleetContext";
import { friendlyMessage, http } from "@/lib/api";
import { money, pct } from "@/lib/format";
import { FriendlyNotice } from "./Offline";
import { StatCard, StatChips } from "./StatCard";
import Timeline from "./Timeline";
import { UnitMap } from "./Maps";
import { UndoBooking } from "./UndoBooking";
import { VanDetailCard } from "./VanDetailCard";
import { PERIODS, SegPills, WEEK_DAYS } from "./SegPills";

function UnitHeader({ unit, dateLabel, period, onPeriod }) {
  const week = period === "week";
  return (
    <div className="dp-rise" data-testid="unit-header">
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div className="min-w-[260px] flex-1">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full" style={{ background: unit.color }} data-testid="unit-header-dot" />
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl" data-testid="unit-header-name">{unit.name}</h1>
          </div>
          <p className="mt-1 text-base text-[var(--dp-ink-2)]" data-testid="unit-header-nickname">{unit.nickname}</p>
          {dateLabel && <p className="mt-1 text-sm text-[var(--dp-ink-3)]">{dateLabel} · Today's route · Driver <span className="font-medium text-[var(--dp-ink-2)]" data-testid="unit-header-driver">{unit.driver_name}</span> · Shift {unit.shift_start_label} to {unit.shift_end_label}</p>}
        </div>
        <div className="flex shrink-0 flex-col items-end gap-3">
          <SegPills options={PERIODS} value={period} onChange={onPeriod} testId="unit-period" size="sm" />
          <div className="flex gap-6">
            <div>
              <p className="text-xs uppercase tracking-wider text-[var(--dp-ink-3)]">Stops today</p>
              <p className="tnum font-display text-3xl font-semibold" data-testid="unit-header-stops">{unit.stops_count}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-[var(--dp-ink-3)]">{week ? "Spare min this week" : "Spare minutes"}</p>
              <p className="tnum font-display text-3xl font-semibold text-[var(--dp-green)]" data-testid="unit-header-spare">{week ? unit.spare_minutes * WEEK_DAYS : unit.spare_minutes}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatsRow({ unit }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3" data-testid="unit-stats-row">
      <StatCard label="Cost per stop" value={money(unit.cost_per_stop)} hint={`${unit.route_minutes} min and ${unit.route_miles} mi of driving day`} testId="unit-stat-cost-per-stop" />
      <StatCard label="Revenue per day" value={money(unit.revenue_per_day)} hint={`From ${unit.stops_count} stops`} testId="unit-stat-revenue-per-day" tone="green" />
      <StatCard label="On time, last 4 weeks" value={pct(unit.on_time_rate)} hint={`${unit.on_time_runs} of ${unit.total_runs} runs inside the window`} testId="unit-stat-on-time-rate" />
    </div>
  );
}

export default function UnitPage({ unitKey }) {
  const { version, fleet } = useFleet();
  const [params] = useSearchParams();
  const previewId = params.get("preview");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [period, setPeriod] = useState("today");

  useEffect(() => {
    let live = true;
    setError("");
    http.get(`/units/${unitKey}`)
      .then(({ data: d }) => live && setData(d))
      .catch((err) => live && setError(friendlyMessage(err, "Couldn't load this van. Try again in a moment.")));
    return () => { live = false; };
  }, [unitKey, version, attempt]);

  if (error) return <FriendlyNotice title="This van didn't load" message={error} onRetry={() => setAttempt((a) => a + 1)} testId="unit-page-error" />;
  if (!data || data.unit.key !== unitKey) {
    return (
      <div className="space-y-4 p-6 md:p-10" data-testid="unit-page-loading">
        <Skeleton className="h-36 rounded-2xl" />
        <Skeleton className="h-24 rounded-2xl" />
        <Skeleton className="h-96 rounded-2xl" />
      </div>
    );
  }
  const { unit, plan, timeline } = data;
  return (
    <div className="mx-auto w-full max-w-5xl space-y-6 p-4 sm:p-6 md:px-8 md:pb-10 md:pt-6" data-testid="unit-page">
      <StatChips testPrefix="unit-chip" items={[
        ["stops", "Stops", unit.stops_count],
        ["spare", period === "week" ? "Spare min this week" : "Spare min", period === "week" ? unit.spare_minutes * WEEK_DAYS : unit.spare_minutes],
        ["cost", "Cost per stop", money(unit.cost_per_stop)],
        ["ontime", "On-time", pct(unit.on_time_rate)],
      ]} />
      <UnitHeader unit={unit} dateLabel={fleet?.business?.demo_date_label} period={period} onPeriod={setPeriod} />
      <UndoBooking unitKey={unitKey} />
      <UnitMap unit={unit} timeline={timeline} previewId={previewId} position={data.position}>
        <VanDetailCard unit={unit} plan={plan} timeline={timeline} position={data.position} insight={data.insight}
          clock={data.demo_clock_minutes} clockLabel={data.demo_clock_label} />
      </UnitMap>
      <StatsRow unit={unit} />
      <div className="dp-card p-5 sm:p-6" data-testid="unit-timeline-card">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">Today's route</h2>
          <span className="flex items-center gap-3 text-xs text-[var(--dp-ink-2)]">
            <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />Demo clock {data.demo_clock_label}</span>
            <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{unit.route_miles} mi</span>
          </span>
        </div>
        <Timeline unit={unit} plan={plan} rows={timeline} clock={data.demo_clock_minutes} clockLabel={data.demo_clock_label} />
      </div>
    </div>
  );
}
