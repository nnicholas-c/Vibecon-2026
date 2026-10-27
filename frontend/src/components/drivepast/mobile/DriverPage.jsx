import { useState } from "react";
import { useParams } from "react-router-dom";
import { Check } from "lucide-react";
import { http } from "@/lib/api";
import { usePoll } from "./usePoll";

function StopRow({ s, i, vanId, onDone }) {
  const [busy, setBusy] = useState(false);
  const done = s.tags?.includes("Done");
  const isNew = s.tags?.includes("New");
  const tap = async () => {
    setBusy(true);
    try { await http.post(`/units/${vanId}/stops/${s.stop_key}/done`); await onDone(); } finally { setBusy(false); }
  };
  return (
    <li className={`flex items-start gap-3 border-b border-[var(--dp-line)] px-4 py-3 ${done ? "opacity-50" : ""} ${isNew ? "bg-[var(--dp-accent-soft,#FFE3D6)]" : ""}`} data-testid={`driver-stop-${i + 1}`}>
      <span className="w-14 shrink-0 font-mono text-sm font-semibold" data-testid={`driver-stop-time-${i + 1}`}>{s.arrival_label}</span>
      <div className="min-w-0 flex-1">
        <p className="flex flex-wrap items-center gap-1.5 text-sm font-semibold">
          <span data-testid={`driver-stop-customer-${i + 1}`}>{s.customer_name}</span>
          {isNew && <span className="bg-[var(--dp-accent)] px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-[#111214]" data-testid={`driver-stop-new-${i + 1}`}>New</span>}
        </p>
        <p className="truncate text-xs text-[var(--dp-ink-2)]">{s.address}</p>
        <p className="font-mono text-[11px] text-[var(--dp-ink-3)]">{s.kind === "dropoff" ? "Drop-off" : "Pickup"} · {s.window_label}</p>
      </div>
      <button type="button" onClick={tap} disabled={busy || done} className="flex h-9 shrink-0 items-center gap-1 border border-[var(--dp-ink)] px-3 text-xs font-semibold disabled:opacity-50" data-testid={`driver-stop-done-${i + 1}`}>
        <Check className="h-3.5 w-3.5" />Done
      </button>
    </li>
  );
}

export default function DriverPage() {
  const { vanId } = useParams();
  const { data, error, load } = usePoll(`/units/${vanId}`, 5000);
  const u = data?.unit;
  return (
    <div className="mx-auto min-h-[100dvh] w-full max-w-[375px] bg-[var(--dp-page)] text-[var(--dp-ink)]" data-testid="driver-page">
      <header className="sticky top-0 z-10 bg-[var(--dp-ink)] px-4 py-3 text-[var(--dp-page)]">
        <p className="font-display text-lg font-bold" data-testid="driver-van-name">{u?.name || "Loading…"}</p>
        <p className="text-xs opacity-80" data-testid="driver-name">{u ? `${u.driver_name} · today's stops` : ""}</p>
      </header>
      {error && <p className="px-4 py-2 text-xs text-[var(--dp-amber)]" data-testid="driver-error">{error}</p>}
      <ol data-testid="driver-stops">
        {(data?.timeline || []).map((s, i) => <StopRow key={s.stop_key} s={s} i={i} vanId={vanId} onDone={load} />)}
      </ol>
    </div>
  );
}
