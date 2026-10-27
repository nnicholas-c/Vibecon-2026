import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { friendlyMessage, http } from "@/lib/api";
import { usePoll } from "./usePoll";

function Reply({ q }) {
  return (
    <div className="ml-auto max-w-[85%] rounded-2xl rounded-br-md bg-[var(--dp-ink)] px-4 py-3 text-sm text-[var(--dp-page)]" data-testid="customer-reply">
      <p data-testid="customer-line">{q.customer_line}</p>
      <p className="mt-2 font-mono text-xs opacity-80" data-testid="customer-times">Pickup about {q.pickup_label}{q.dropoff_label ? ` · drop-off about ${q.dropoff_label}` : ""}</p>
    </div>
  );
}

// "Books automatically in N s", counting down to the server's commit_at.
function Countdown({ at, onZero }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(t);
  }, []);
  const left = Math.max(0, Math.ceil((new Date(at).getTime() - now) / 1000));
  useEffect(() => { if (left === 0) onZero(); }, [left, onZero]);
  return <p className="font-mono text-xs text-[var(--dp-ink-2)]" data-testid="customer-countdown">{left > 0 ? `Books automatically in ${left} s` : "Booking now…"}</p>;
}

export default function CustomerPage() {
  const { requestKey } = useParams();
  const { data, load } = usePoll(`/customer/${requestKey}`, 3000);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const q = data?.quote;
  const act = async (what) => {
    setBusy(true); setError("");
    try { await http.post(`/quotes/${q.key}/${what}`, {}, { timeout: 30000 }); } catch (err) { setError(friendlyMessage(err, "That didn't go through. Try again.")); }
    await load();
    setBusy(false);
  };
  return (
    <div className="mx-auto flex min-h-[100dvh] w-full max-w-[375px] flex-col gap-3 bg-[var(--dp-page)] px-4 py-5 text-[var(--dp-ink)]" data-testid="customer-page">
      <p className="text-center font-mono text-[11px] uppercase tracking-wider text-[var(--dp-ink-3)]">Bayline Courier</p>
      {data && <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-bl-md bg-[#DCDAD4] px-4 py-3 text-sm" data-testid="customer-request-text">{data.text}</div>}
      {q && <Reply q={q} />}
      {data?.booked_line && <p className="text-sm font-semibold text-[var(--dp-green)]" data-testid="customer-booked-line">{data.booked_line}</p>}
      {data?.confirmation && <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-bl-md bg-[#DCDAD4] px-4 py-3 text-sm" data-testid="customer-confirmation">{data.confirmation}</div>}
      {q?.status === "declined" && <p className="text-sm font-semibold text-[var(--dp-ink-2)]" data-testid="customer-declined-line">Declined.</p>}
      {q?.status === "sent" && q.commit_at && <Countdown at={q.commit_at} onZero={load} />}
      {q?.status === "sent" && (
        <div className="flex gap-2" data-testid="customer-actions">
          <button type="button" onClick={() => act("accept")} disabled={busy} className="h-11 flex-1 bg-[var(--dp-ink)] text-sm font-bold text-[var(--dp-page)] disabled:opacity-50" data-testid="customer-accept-button">Accept</button>
          <button type="button" onClick={() => act("decline")} disabled={busy} className="h-11 flex-1 border border-[var(--dp-ink)] text-sm font-bold disabled:opacity-50" data-testid="customer-decline-button">Decline</button>
        </div>
      )}
      {data && !q && <p className="text-xs text-[var(--dp-ink-3)]" data-testid="customer-waiting">Waiting for Bayline's reply…</p>}
      {error && <p className="text-xs text-[var(--dp-amber)]" role="alert" data-testid="customer-error">{error}</p>}
    </div>
  );
}
