import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { http } from "@/lib/api";

const shell = "min-h-[100dvh] bg-[var(--dp-page)] px-5 py-10 text-[var(--dp-ink)]";

export default function QuotePage() {
  const { token } = useParams();
  const [params] = useSearchParams();
  const [q, setQ] = useState(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    http.get(`/q/${token}`).then(({ data }) => { setQ(data); if (data.message) setMsg(data.message); })
      .catch((err) => setMsg(err?.response?.data?.message || "This link isn't valid."));
  }, [token]);
  const answer = async (action) => {
    setBusy(true);
    try { setMsg((await http.post(`/q/${token}/${action}`)).data.message); }
    catch (err) { setMsg(err?.response?.data?.message || "Something went wrong. Try again."); }
    finally { setBusy(false); }
  };
  const want = params.get("a") === "decline" ? "decline" : "accept";
  return (
    <div className={shell} data-testid="quote-page">
      <div className="mx-auto w-full max-w-md space-y-5">
        <p className="text-sm font-semibold text-[var(--dp-ink)]">Bayline Courier</p>
        {q?.valid && (
          <div className="dp-sign space-y-2" data-testid="quote-page-card">
            <p className="tnum text-2xl font-bold" data-testid="quote-page-price">{q.price_text} <span className="text-base font-medium text-[var(--dp-ink-2)]">{q.per}</span></p>
            <p className="tnum text-sm text-[var(--dp-ink-2)]">Pickup about {q.pickup_label}</p>
            <p className="text-sm">{q.customer_line}</p>
          </div>
        )}
        {msg ? (
          <p className="dp-card p-5 text-base font-semibold" role="status" data-testid="quote-page-message">{msg}</p>
        ) : q?.open && (
          <div className="flex flex-col gap-3">
            <p className="text-sm text-[var(--dp-ink-2)]">{want === "accept" ? "Tap to confirm and book it." : "Tap to say no thanks."}</p>
            <button type="button" disabled={busy} onClick={() => answer(want)} data-testid={`quote-page-${want}-button`}
              className={`h-12 rounded-full text-base font-bold ${want === "accept" ? "bg-[var(--dp-ink)] text-[var(--dp-surface)]" : "border border-[var(--dp-ink)] bg-[var(--dp-surface)]"}`}>
              {busy ? "One moment..." : want === "accept" ? "Confirm and book" : "Decline"}
            </button>
            <button type="button" disabled={busy} onClick={() => answer(want === "accept" ? "decline" : "accept")} className="text-sm text-[var(--dp-ink-2)] underline" data-testid={`quote-page-${want === "accept" ? "decline" : "accept"}-button`}>
              {want === "accept" ? "Decline instead" : "Accept instead"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
