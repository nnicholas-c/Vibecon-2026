import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Skeleton } from "@/components/ui/skeleton";
import { useFleet } from "@/context/FleetContext";
import { money, pct } from "@/lib/format";
import { FriendlyNotice } from "./Offline";
import { StatChips } from "./StatCard";
import { FleetMap } from "./Maps";
import { PERIODS, SegPills, WEEK_DAYS } from "./SegPills";
import { SavedBump } from "./SavedBump";

const TAGLINE = "Price every job from the van that already drives past.";

function fleetOnTime(units) {
  const runs = units.reduce((a, u) => a + (u.total_runs || 0), 0);
  const good = units.reduce((a, u) => a + (u.on_time_runs || 0), 0);
  return runs ? pct((100 * good) / runs) : "--";
}

function FleetTable({ units, onOpen }) {
  const most = Math.max(...units.map((u) => u.spare_minutes));
  const th = "px-4 py-3 text-xs font-medium uppercase tracking-wider text-[var(--dp-ink-3)]";
  return (
    <div className="dp-card overflow-x-auto" data-testid="dispatch-units-table">
      <table className="w-full min-w-[560px] text-sm">
        <thead className="border-b border-[var(--dp-line)] text-left">
          <tr>
            <th className={th}>Van</th>
            <th className={`${th} text-right`}>Stops</th>
            <th className={`${th} text-right`}>Spare min</th>
            <th className={`${th} text-right`}>Revenue / day</th>
            <th className={`${th} text-right`}>Cost / stop</th>
            <th className={`${th} text-right`}>On time</th>
          </tr>
        </thead>
        <tbody>
          {units.map((u) => (
            <tr key={u.key} onClick={() => onOpen(u.key)} className="cursor-pointer border-b border-[var(--dp-line)] transition-colors last:border-0 hover:bg-[var(--dp-bg)]" data-testid={`dispatch-row-${u.key}`}>
              <td className="px-4 py-3.5">
                <span className="flex items-center gap-2.5">
                  <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: u.color }} />
                  <span className="whitespace-nowrap font-medium" data-testid={`dispatch-name-${u.key}`}>{u.name}</span>
                  <span className="hidden whitespace-nowrap text-[var(--dp-ink-2)] xl:inline">{u.nickname}</span>
                </span>
              </td>
              <td className="tnum px-4 py-3.5 text-right" data-testid={`dispatch-stops-${u.key}`}>{u.stops_count}</td>
              <td className="tnum px-4 py-3.5 text-right">
                {u.spare_minutes === most && <span className="mr-2 rounded-full bg-[var(--dp-green-soft)] px-2 py-0.5 text-[11px] font-medium text-[var(--dp-green)]" data-testid={`dispatch-most-spare-${u.key}`}>Most</span>}
                <span className="font-semibold" data-testid={`dispatch-spare-${u.key}`}>{u.spare_minutes}</span>
              </td>
              <td className="tnum px-4 py-3.5 text-right text-[var(--dp-green)]" data-testid={`dispatch-revenue-${u.key}`}>{money(u.revenue_per_day)}</td>
              <td className="tnum px-4 py-3.5 text-right" data-testid={`dispatch-cost-${u.key}`}>{money(u.cost_per_stop)}</td>
              <td className="tnum px-4 py-3.5 text-right" data-testid={`dispatch-ontime-${u.key}`}>{pct(u.on_time_rate)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function DispatchPage() {
  const { fleet, error, reload, live } = useFleet();
  const navigate = useNavigate();
  const [period, setPeriod] = useState("today");
  if (!fleet && error) return <FriendlyNotice title="The fleet didn't load" message={error} onRetry={reload} testId="dispatch-error" />;
  if (!fleet) {
    return (
      <div className="space-y-4 p-6 md:p-10" data-testid="dispatch-loading">
        <Skeleton className="h-20 rounded-2xl" />
        <Skeleton className="h-64 rounded-2xl" />
      </div>
    );
  }
  const { business, units, totals } = fleet;
  const week = period === "week";
  const spare = week ? totals.spare_minutes * WEEK_DAYS : totals.spare_minutes;
  return (
    <div className="mx-auto w-full max-w-5xl space-y-8 p-4 sm:p-6 md:px-8 md:pb-10 md:pt-6" data-testid="dispatch-page">
      <div className="dp-rise flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">Fleet today</h1>
          <p className="mt-2 text-sm text-[var(--dp-ink-3)]"><span data-testid="dispatch-demo-date">{business.demo_date_label}, {business.demo_clock_label}</span> · Today's routes</p>
          <p className="mt-3 text-base text-[var(--dp-ink-2)]" data-testid="app-tagline">{TAGLINE}</p>
          <Link to="/research" className="mt-2 inline-block text-sm font-semibold underline" data-testid="dispatch-research-link">Our research</Link>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <SegPills options={PERIODS} value={period} onChange={setPeriod} testId="dispatch-period" />
        </div>
      </div>
      <StatChips testPrefix="dispatch-chip" items={[
        ["vans", "Vans", units.length],
        ["stops", "Stops today", totals.stops],
        ["spare", week ? "Spare min this week" : "Spare min", spare],
        ["ontime", "On-time", fleetOnTime(units)],
        ["saved", "Saved customers", <>{`$${Math.round(live?.saved_today ?? 0)} today`}<SavedBump value={live?.saved_today} /></>, true],
        ["new", "New stops", totals.new_stops ?? 0],
      ]} />
      <div className="space-y-3">
        <h2 className="text-base font-semibold md:text-lg">Fleet map</h2>
        <FleetMap />
      </div>
      <div className="space-y-3">
        <h2 className="text-base font-semibold md:text-lg">Vans</h2>
        <FleetTable units={units} onOpen={(k) => navigate(`/units/${k}`)} />
      </div>
    </div>
  );
}
