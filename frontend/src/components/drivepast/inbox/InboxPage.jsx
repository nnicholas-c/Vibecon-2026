import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { FileSpreadsheet, FileText, Image, Mail, MessageSquare, Voicemail } from "lucide-react";
import { ImportJobs } from "./ImportJobs";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useFleet } from "@/context/FleetContext";
import { friendlyMessage, http } from "@/lib/api";
import { AiTag } from "../OptionCards";
import { AddRequest } from "./AddRequest";
import RequestPage from "./RequestPage";
import { GmailBar } from "./GmailBar";

export const SOURCE_ICON = { email: Mail, gmail: Mail, text: MessageSquare, pdf: FileText, voicemail: Voicemail, photo: Image, sheet: FileSpreadsheet, csv: FileSpreadsheet };
const CHIP = {
  new: "bg-[var(--dp-bg)] text-[var(--dp-ink-2)]", reading: "bg-[var(--dp-bg)] text-[var(--dp-ink-2)] animate-pulse", needs_info: "bg-[var(--dp-amber-soft)] text-[var(--dp-amber)]",
  priced: "bg-[var(--dp-green-soft)] text-[var(--dp-green)]", quoted: "bg-[var(--dp-bg)] text-[var(--dp-ink)]",
  accepted: "bg-[var(--dp-green-soft)] text-[var(--dp-green)]", booked: "bg-[var(--dp-green-soft)] text-[var(--dp-green)]", declined: "bg-[var(--dp-bg)] text-[var(--dp-ink-3)]",
};

export const bookedIn = (s) => (s >= 60 ? `Booked in ${Math.floor(s / 60)} min ${s % 60} s` : `Booked in ${s} s`);

// "Auto-sent within your rules", linking to the Demo mode setting.
export function AutoSentLink({ testId }) {
  return (
    <Link to="/settings#auto-send" onClick={(e) => e.stopPropagation()} className="font-mono text-[10px] uppercase tracking-wider text-[var(--dp-ink-2)] underline underline-offset-2" data-testid={testId}>
      Auto-sent within your rules
    </Link>
  );
}

export function StatusChip({ status, label, testId }) {
  return <span className={`whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold ${CHIP[status] || CHIP.new}`} data-testid={testId}>{label}</span>;
}

const SOURCE_LABEL = { gmail: "Gmail", email: "Email", text: "Text", photo: "Photo", voicemail: "Voicemail", pdf: "PDF", sheet: "Sheet", csv: "CSV" };
const TIME = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", timeZone: "America/Los_Angeles" });
const sourceLabel = (r) => (r.sender === "Pasted request" || r.source === "email" && !r.sender_contact ? "Manual" : SOURCE_LABEL[r.source] || r.source);

function Row({ r, active, onOpen }) {
  const Icon = SOURCE_ICON[r.source] || Mail;
  return (
    <button onClick={onOpen} data-testid={`inbox-row-${r.number}`}
      className={`w-full rounded-2xl border px-4 py-3 text-left transition-colors ${active ? "border-[var(--dp-ink)] bg-[rgba(255,91,31,0.14)]" : "border-transparent hover:bg-[var(--dp-bg)]"}`}>
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 shrink-0 text-[var(--dp-ink-2)]" aria-label={r.source} />
        <span className="font-mono text-[11px] uppercase text-[var(--dp-ink-3)]" data-testid={`inbox-row-source-${r.number}`}>{sourceLabel(r)}</span>
        <span className="min-w-0 flex-1 truncate text-sm font-semibold" data-testid={`inbox-row-sender-${r.number}`}>{r.sender}</span>
        <StatusChip status={r.status} label={r.status_label} testId={`inbox-row-status-${r.number}`} />
      </div>
      <p className="mt-1.5 line-clamp-2 text-sm text-[var(--dp-ink-2)]" data-testid={`inbox-row-summary-${r.number}`}>{r.summary}</p>
      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
        {r.status === "booked" && r.booked_seconds != null && <span className="font-mono text-[11px] text-[var(--dp-green)]" data-testid={`inbox-row-booked-in-${r.number}`}>{bookedIn(r.booked_seconds)}</span>}
        {r.booked_by && <span className="bg-[var(--dp-green-soft)] px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-[var(--dp-green)]" data-testid={`inbox-row-booked-by-${r.number}`}>{r.booked_by}</span>}
        {r.auto_sent && <AutoSentLink testId={`inbox-row-auto-sent-${r.number}`} />}
        {r.received_at && <span className="font-mono text-[11px] text-[var(--dp-ink-3)]" data-testid={`inbox-row-received-${r.number}`}>{TIME.format(new Date(r.received_at))}</span>}
        {r.group && <span className="rounded-full bg-[var(--dp-bg)] px-2 py-0.5 text-[11px] font-semibold text-[var(--dp-ink-2)]" data-testid={`inbox-row-part-${r.number}`}>{r.group.part} of {r.group.of}</span>}
      </div>
    </button>
  );
}

export default function InboxPage() {
  const { requestKey } = useParams();
  const navigate = useNavigate();
  const { reload, version } = useFleet();
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const { data } = await http.get("/inbox");
      setRows(data.requests);
      setError("");
    } catch (err) {
      setError(friendlyMessage(err, "Couldn't load the inbox. Try again."));
    }
  };
  useEffect(() => { load(); }, [version]);
  useEffect(() => {
    const t = setInterval(() => { if (document.visibilityState === "visible") load(); }, 5000);
    return () => clearInterval(t);
  }, []);
  const refresh = async () => { await load(); reload(); };

  return (
    <div className="flex min-h-full flex-col lg:flex-row" data-testid="inbox-page">
      <div className={`${requestKey ? "hidden lg:flex" : "flex"} w-full flex-col gap-4 border-[var(--dp-line)] p-4 sm:p-6 lg:w-[380px] lg:shrink-0 lg:border-r`}>
        <div className="dp-rise">
          <h1 className="text-3xl font-bold tracking-tight">Inbox</h1>
          <p className="mt-1 text-sm text-[var(--dp-ink-3)]">Every request that came in, and what we read from it.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <AddRequest onAdded={async (r) => { await refresh(); navigate(`/inbox/${r.key}`); }} />
          <ImportJobs onImported={refresh} />
        </div>
        {error && <p className="text-sm text-[var(--dp-amber)]" role="alert" data-testid="inbox-error">{error}</p>}
        <GmailBar />
        {!rows && !error && <Skeleton className="h-64 rounded-2xl" />}
        <div className="space-y-1.5" data-testid="inbox-list">
          {(rows || []).map((r) => <Row key={r.key} r={r} active={r.key === requestKey} onOpen={() => navigate(`/inbox/${r.key}`)} />)}
        </div>
      </div>
      <div className={`${requestKey ? "flex" : "hidden lg:flex"} min-w-0 flex-1 flex-col`}>
        {requestKey ? <RequestPage key={requestKey} requestKey={requestKey} onChanged={refresh} /> : (
          <div className="m-auto p-10 text-center text-sm text-[var(--dp-ink-3)]" data-testid="inbox-empty-detail">Pick a request to see what was read from it.</div>
        )}
      </div>
    </div>
  );
}
