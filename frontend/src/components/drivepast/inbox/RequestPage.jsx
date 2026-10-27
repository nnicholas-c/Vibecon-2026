import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, ArrowLeft, Ban, HelpCircle, RefreshCw, Truck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { friendlyMessage, http } from "@/lib/api";
import { money } from "@/lib/format";
import { toast } from "sonner";
import { useFleet } from "@/context/FleetContext";
import { UndoBooking } from "../UndoBooking";
import { AiTag, OptionCards } from "../OptionCards";
import { AutoSentLink, SOURCE_ICON, StatusChip, bookedIn } from "./InboxPage";

const MARK = {
  high: "bg-[var(--dp-green-soft)] text-[var(--dp-green)]", medium: "bg-[var(--dp-bg)] text-[var(--dp-ink-2)]",
  low: "bg-[var(--dp-amber-soft)] text-[var(--dp-amber)]",
};

function Flag({ testId }) {
  return <span className="inline-flex items-center gap-1 rounded-full bg-[var(--dp-amber-soft)] px-2 py-0.5 text-[11px] font-semibold text-[var(--dp-amber)]" data-testid={testId}><HelpCircle className="h-3 w-3" />Needs clarification</span>;
}

function Detail({ d }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-[var(--dp-line)] py-3 last:border-0" data-testid={`detail-${d.key}`}>
      <div className="min-w-0">
        <p className="text-xs uppercase tracking-wider text-[var(--dp-ink-3)]">{d.label}</p>
        <p className="tnum mt-0.5 text-sm font-medium" data-testid={`detail-${d.key}-value`}>{d.value}</p>
        {d.as_written && d.as_written !== d.value && <p className="mt-0.5 text-xs text-[var(--dp-ink-3)]">As written: "{d.as_written}"</p>}
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1">
        <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize ${MARK[d.confidence]}`} data-testid={`detail-${d.key}-confidence`}>{d.confidence}</span>
        {d.needs_clarification && <Flag testId={`detail-${d.key}-flag`} />}
      </div>
    </div>
  );
}

function RawRequest({ r }) {
  const Icon = SOURCE_ICON[r.source];
  const [blob, setBlob] = useState(null);
  useEffect(() => {
    if (!r.file) return undefined;
    let url;
    http.get(r.file.url.replace(/^\/api/, ""), { responseType: "blob" }).then(({ data }) => { url = URL.createObjectURL(data); setBlob(url); }).catch(() => {});
    return () => url && URL.revokeObjectURL(url);
  }, [r.file]);
  return (
    <section className="dp-card space-y-3 p-5" data-testid="request-raw">
      <p className="flex items-center gap-2 text-xs uppercase tracking-wider text-[var(--dp-ink-3)]">{Icon && <Icon className="h-3.5 w-3.5" />}The request, as sent</p>
      {r.file && (
        <div className="space-y-2" data-testid="request-file">
          {r.file.content_type.startsWith("image/") && blob && <img src={blob} alt="Uploaded request" className="max-h-80 rounded-xl" />}
          {blob && <a href={blob} target="_blank" rel="noreferrer" className="text-sm font-semibold text-[var(--dp-green)] underline" data-testid="request-file-link">{r.file.name}</a>}
          {!blob && <p className="text-sm text-[var(--dp-ink-2)]">{r.file.name}</p>}
          {r.raw_text && <p className="text-xs uppercase tracking-wider text-[var(--dp-ink-3)]">Text taken from the file</p>}
        </div>
      )}
      {r.raw_text && <p className="whitespace-pre-wrap text-sm leading-relaxed" data-testid="request-raw-text">{r.raw_text}</p>}
    </section>
  );
}

function Problems({ problems }) {
  if (!problems?.length) return null;
  return (
    <div className="space-y-2" data-testid="request-problems">
      {problems.map((p, i) => (
        <p key={p.text} className="flex items-start gap-2 rounded-xl bg-[var(--dp-amber-soft)] px-3 py-2.5 text-sm font-medium text-[var(--dp-amber)]" data-testid={`request-problem-${i}`}>
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />{p.text}
        </p>
      ))}
    </div>
  );
}

function Question({ q, onChange }) {
  return (
    <div className="dp-card space-y-2 p-5" data-testid="request-question">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wider text-[var(--dp-ink-3)]">Question for the customer</p>
        <AiTag tag={null} testId="request-question-tag" />
      </div>
      <textarea value={q.text} onChange={(e) => onChange(e.target.value)} rows={3} data-testid="request-question-input"
        className="w-full rounded-xl border border-[var(--dp-line)] bg-[var(--dp-surface)] p-3 text-sm outline-none focus:border-[var(--dp-green)]" />
    </div>
  );
}

// Shown while the request is being read in the background.
function ReadingSkeleton({ vans }) {
  const [pricing, setPricing] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setPricing(true), 2500);
    return () => clearTimeout(t);
  }, []);
  return (
    <section className="dp-card space-y-3 p-5" data-testid="request-reading">
      <p className="text-sm font-semibold" data-testid="request-reading-text">{pricing ? `Pricing against ${vans} vans` : "Reading the request"}</p>
      <Skeleton className="h-5 w-3/4" /><Skeleton className="h-5 w-2/3" /><Skeleton className="h-5 w-1/2" /><Skeleton className="h-16 w-full" />
    </section>
  );
}

export default function RequestPage({ requestKey, onChanged }) {
  const navigate = useNavigate();
  const [r, setR] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [vans, setVans] = useState(null);
  const [question, setQuestion] = useState(null);
  const { version, phonesOpen, fleet } = useFleet();

  const load = useCallback(async () => {
    try {
      const { data } = await http.get(`/inbox/${requestKey}`);
      setR(data);
      if (data.question) setQuestion(data.question);
    } catch (err) {
      setError(friendlyMessage(err, "Couldn't load this request."));
    }
  }, [requestKey]);
  useEffect(() => { load(); }, [load, version]);
  const live = phonesOpen || r?.status === "quoted" || r?.status === "reading" || (r && !r.details);
  useEffect(() => {
    if (!live) return undefined;
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, [live, load]);

  const act = async (label, fn) => {
    setBusy(label);
    setError("");
    try {
      await fn();
    } catch (err) {
      setError(friendlyMessage(err, "Couldn't read that right now. Try again."));
    } finally {
      setBusy("");
    }
  };
  const read = () => act("read", async () => { const { data } = await http.post(`/inbox/${requestKey}/read`, {}, { timeout: 90000 }); setR(data); setVans(null); onChanged(); });
  const askVans = () => act("vans", async () => { const { data } = await http.post(`/inbox/${requestKey}/ask-vans`, {}, { timeout: 90000 }); setVans(data); await load(); onChanged(); });
  const askCustomer = () => act("customer", async () => { const { data } = await http.post(`/inbox/${requestKey}/ask-customer`, {}, { timeout: 90000 }); setQuestion(data.question || { text: data.message, tag: null }); await load(); });
  const decline = () => act("decline", async () => { await http.post(`/inbox/${requestKey}/decline`); await load(); onChanged(); });
  const { setPhonesOpen } = useFleet();
  const sendOption = (o, confirm) => act("send", async () => {
    await http.post(`/inbox/${requestKey}/send`, { option_id: o.option_id, confirm_loss: confirm });
    toast.success("Sent to the Customer phone");
    await load();
    onChanged();
  });
  const rejectOption = (o) => act("reject", async () => {
    const { data } = await http.post(`/inbox/${requestKey}/reject-option`, { option_id: o.option_id });
    setVans((v) => ({ ...(v || { priceable: true }), options: data.options }));
  });
  const sendQuestion = () => act("question", async () => {
    await http.post(`/inbox/${requestKey}/send-question`, { text: question.text });
    toast.success("Question sent to the Customer phone");
    await load();
  });
  const shownOptions = vans?.options || (r?.status === "quoted" || r?.status === "priced" || r?.status === "needs_info" ? r?.options : null);

  if (!r) return error ? <p className="p-6 text-sm text-[var(--dp-amber)]">{error}</p> : <div className="p-6"><Skeleton className="h-96 rounded-2xl" /></div>;
  const read_ = Boolean(r.details?.length);

  return (
    <div className="space-y-5 p-4 sm:p-6 md:p-8" data-testid="request-page">
      <button onClick={() => navigate("/inbox")} className="inline-flex items-center gap-1 text-sm text-[var(--dp-ink-2)] lg:hidden" data-testid="request-back-button"><ArrowLeft className="h-4 w-4" />Inbox</button>
      <header className="dp-rise flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm text-[var(--dp-ink-3)]">
            Request {r.number} · {r.source}
            {r.group && (
              <span data-testid="request-part">
                {" · "}{r.group.part} of {r.group.of}
                {r.group.keys.filter((k) => k !== r.key).map((k) => (
                  <button key={k} onClick={() => navigate(`/inbox/${k}`)} className="ml-2 font-semibold text-[var(--dp-green)] underline" data-testid={`request-linked-${k}`}>
                    See part {r.group.keys.indexOf(k) + 1}
                  </button>
                ))}
              </span>
            )}
          </p>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl" data-testid="request-sender">{r.sender}</h1>
          {r.source === "gmail" && <p className="text-sm text-[var(--dp-ink-2)]" data-testid="request-gmail-from">Gmail · {r.sender_contact}{r.gmail?.subject ? ` · ${r.gmail.subject}` : ""}</p>}
          {r.summary && <p className="mt-1 max-w-2xl text-sm text-[var(--dp-ink-2)]" data-testid="request-summary">{r.summary}</p>}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {r.needs_clarification && <Flag testId="request-needs-clarification" />}
          <StatusChip status={r.status} label={r.status_label} testId="request-status" />
          {r.status === "booked" && r.booked_seconds != null && <span className="font-mono text-xs text-[var(--dp-green)]" data-testid="request-booked-in">{bookedIn(r.booked_seconds)}</span>}
          {r.booked_by && <span className="bg-[var(--dp-green-soft)] px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-[var(--dp-green)]" data-testid="request-booked-by">{r.booked_by}</span>}
          {r.auto_sent && <AutoSentLink testId="request-auto-sent" />}
        </div>
      </header>
      <div className="flex flex-wrap gap-2">
        <Button onClick={askVans} disabled={Boolean(busy)} className="h-10 rounded-full px-4 font-semibold" data-testid="request-ask-vans-button"><Truck className="mr-2 h-4 w-4" />{busy === "vans" ? "Asking..." : "Ask the vans"}</Button>
        <Button onClick={askCustomer} disabled={Boolean(busy)} variant="outline" className="h-10 rounded-full px-4 font-semibold" data-testid="request-ask-customer-button"><HelpCircle className="mr-2 h-4 w-4" />{busy === "customer" ? "Drafting..." : "Ask the customer"}</Button>
        <Button onClick={decline} disabled={Boolean(busy) || r.status === "declined"} variant="outline" className="h-10 rounded-full px-4 font-semibold" data-testid="request-decline-button"><Ban className="mr-2 h-4 w-4" />Decline</Button>
        <Button onClick={read} disabled={Boolean(busy) || r.status === "reading"} variant="ghost" className="h-10 rounded-full px-4" data-testid="request-reread-button"><RefreshCw className={`mr-2 h-4 w-4 ${busy === "read" ? "animate-spin" : ""}`} />Re-read</Button>
      </div>
      {error && (
        <div className="flex items-center gap-3 rounded-xl bg-[var(--dp-amber-soft)] px-3 py-2.5 text-sm text-[var(--dp-amber)]" role="alert" data-testid="request-error">
          {error}<button onClick={read} className="font-semibold underline" data-testid="request-retry-button">Retry</button>
        </div>
      )}
      {r.read_error && <p className="rounded-xl bg-[var(--dp-amber-soft)] px-3 py-2.5 text-sm text-[var(--dp-amber)]" data-testid="request-read-error">{r.read_error}</p>}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <RawRequest r={r} />
        {r.status === "reading" ? <ReadingSkeleton vans={fleet?.units?.length || 0} /> : (
          <section className="dp-card p-5" data-testid="request-details">
            <p className="text-xs uppercase tracking-wider text-[var(--dp-ink-3)]">What we read</p>
            {read_ ? r.details.map((d) => <Detail key={d.key} d={d} />) : <p className="mt-3 text-sm text-[var(--dp-ink-2)]" data-testid="request-not-read">Not read yet. Press "Re-read".</p>}
            <div className="mt-3"><Problems problems={r.problems} /></div>
          </section>
        )}
      </div>
      {question && question.text && <Question q={question} onChange={(text) => setQuestion({ ...question, text })} />}
      {question && question.text && question.tag !== undefined && (
        <div className="flex items-center gap-3">
          <Button onClick={sendQuestion} disabled={Boolean(busy)} className="h-10 rounded-full px-4 font-semibold" data-testid="request-question-send-button">{busy === "question" ? "Sending..." : "Send"}</Button>
          {question.sent && <span className="text-sm text-[var(--dp-green)]" data-testid="request-question-sent">Sent to the Customer phone</span>}
        </div>
      )}
      {r.quote && (
        <div className="dp-card flex flex-wrap items-center justify-between gap-3 px-5 py-3" data-testid="request-quote">
          <p className="tnum text-sm">Quote: <span className="font-semibold">{money(r.quote.price)}</span> on {r.quote.unit_name}, pickup about {r.quote.pickup_label}</p>
          <div className="flex items-center gap-2">
            <StatusChip status={r.quote.status === "sent" ? "quoted" : r.quote.status} label={{ sent: "Sent", accepted: "Booked", declined: "Declined", stale: "Slot filled" }[r.quote.status] || r.quote.status} testId="request-quote-status" />
            <Button variant="outline" onClick={() => setPhonesOpen(true)} className="h-9 rounded-full px-4" data-testid="request-open-phones-button">Open Demo phones</Button>
          </div>
          {r.quote.status === "stale" && <p className="w-full text-sm font-medium text-[var(--dp-amber)]" data-testid="request-quote-stale">This slot is no longer free. Price it again.</p>}
          {r.quote.email_note && <p className="w-full text-sm text-[var(--dp-ink-2)]" data-testid="request-quote-email-note">{r.quote.email_note}</p>}
        </div>
      )}
      <UndoBooking requestKey={requestKey} onDone={load} />
      {vans && !vans.priceable && <p className="rounded-xl bg-[var(--dp-amber-soft)] px-3 py-2.5 text-sm font-medium text-[var(--dp-amber)]" data-testid="request-cant-price">{vans.reason}</p>}
      {shownOptions && !["accepted", "booked"].includes(r.status) && <OptionCards options={shownOptions} prefix="request" actions={{ onSend: sendOption, onReject: rejectOption, busy: Boolean(busy) }} />}
    </div>
  );
}
