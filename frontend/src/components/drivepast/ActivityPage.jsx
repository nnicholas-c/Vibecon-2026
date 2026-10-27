import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { RefreshCw } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { friendlyMessage, http } from "@/lib/api";

const ACTOR = {
  owner: "bg-[var(--dp-ink)] text-[var(--dp-surface)]",
  customer: "bg-[var(--dp-green-soft)] text-[var(--dp-green)]",
  assistant: "bg-[var(--dp-accent)] text-[var(--dp-ink)]",
  driver: "bg-[var(--dp-amber-soft)] text-[var(--dp-amber)]",
  auto: "bg-[var(--dp-bg)] text-[var(--dp-ink)] border border-[var(--dp-ink)]",
};
const TIME = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", timeZone: "America/Los_Angeles" });

function EventRow({ e, i }) {
  const id = `activity-row-${i}`;
  return (
    <li className="grid grid-cols-[72px_96px_minmax(0,1fr)] items-baseline gap-3 border-t border-[var(--dp-line)] px-4 py-3 first:border-t-0" data-testid={id}>
      <span className="font-mono text-xs tabular-nums text-[var(--dp-ink-3)]" data-testid={`${id}-time`}>{TIME.format(new Date(e.ts))}</span>
      <span className={`justify-self-start px-2 py-0.5 font-mono text-[11px] font-semibold uppercase tracking-wider ${ACTOR[e.actor] || ACTOR.owner}`} data-testid={`${id}-actor`}>
        {e.actor}
      </span>
      <span className="min-w-0 text-sm">
        <span data-testid={`${id}-line`}>{e.line}</span>
        {e.kind === "auto_sent" && <Link to="/settings#auto-send" className="ml-2 font-mono text-[11px] uppercase tracking-wider underline underline-offset-2" data-testid={`${id}-auto-sent-link`}>Setting</Link>}
        {e.tool && <span className="ml-2 font-mono text-xs text-[var(--dp-ink-3)]" data-testid={`${id}-tool`}>{e.tool}</span>}
      </span>
    </li>
  );
}

export default function ActivityPage() {
  const [events, setEvents] = useState(null);
  const [error, setError] = useState("");
  const load = async () => {
    try {
      const { data } = await http.get("/activity");
      setEvents(data.events);
      setError("");
    } catch (err) {
      setError(friendlyMessage(err, "Couldn't load the activity. Try again."));
    }
  };
  useEffect(() => { load(); }, []);

  return (
    <div className="mx-auto w-full max-w-4xl space-y-6 p-4 md:p-8" data-testid="activity-page">
      <div className="flex items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight" data-testid="activity-title">Activity</h1>
          <p className="mt-2 text-sm text-[var(--dp-ink-2)]">Everything that happened, newest first.</p>
        </div>
        <button onClick={load} data-testid="activity-refresh-button"
          className="inline-flex h-11 items-center gap-1.5 border border-[var(--dp-ink)] bg-[var(--dp-surface)] px-4 text-sm font-semibold">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>
      {error && <p className="text-sm text-[var(--dp-red)]" data-testid="activity-error">{error}</p>}
      {!events && !error && <Skeleton className="h-24 w-full" />}
      {events && events.length === 0 && (
        <p className="border border-[var(--dp-line)] bg-[var(--dp-surface)] px-4 py-6 text-sm text-[var(--dp-ink-2)]" data-testid="activity-empty">
          Nothing has happened yet today.
        </p>
      )}
      {events && events.length > 0 && (
        <ol className="border border-[var(--dp-ink)] bg-[var(--dp-surface)]" data-testid="activity-list">
          {events.map((e, i) => <EventRow key={e.id} e={e} i={i} />)}
        </ol>
      )}
    </div>
  );
}
