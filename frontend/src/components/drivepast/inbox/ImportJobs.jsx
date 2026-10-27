import { useEffect, useRef, useState } from "react";
import { FileSpreadsheet, RefreshCw, Upload } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { friendlyMessage, http } from "@/lib/api";

const READ_FAIL = "We couldn't read that sheet. Check the link or the file.";
const NONE = "__none__";

function MatchTable({ draft, mapping, setMapping }) {
  return (
    <div className="space-y-3" data-testid="import-match">
      <p className="text-sm text-[var(--dp-ink-2)]" data-testid="import-match-by">
        {draft.name} · {draft.row_count} rows · columns matched {draft.mapped_by === "ai" ? "by AI" : "by header keywords"}. Check them, then import.
      </p>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {draft.fields.map((f) => (
          <label key={f.id} className="flex flex-col gap-1 text-xs font-medium uppercase tracking-wider text-[var(--dp-ink-3)]">
            {f.label}
            <select value={mapping[f.id] || NONE} onChange={(e) => setMapping({ ...mapping, [f.id]: e.target.value === NONE ? undefined : e.target.value })}
              data-testid={`import-map-${f.id}`} className="h-10 border border-[var(--dp-ink)] bg-[var(--dp-surface)] px-2 text-sm normal-case tracking-normal text-[var(--dp-ink)]">
              <option value={NONE}>Not in this sheet</option>
              {draft.headers.map((h) => <option key={h} value={h}>{h}</option>)}
            </select>
          </label>
        ))}
      </div>
    </div>
  );
}

const CLOCK = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", timeZone: "America/Los_Angeles" });

// The backend sheet_poller's last run (every 30 s).
function AutoSyncLine({ info }) {
  const run = info.last_auto_sync;
  const text = !info.sheet_connected ? "No sheet connected"
    : !run ? "Waiting for the first automatic sync"
    : run.error || `Last synced ${CLOCK.format(new Date(run.at)).replace(" ", "").toLowerCase()}: ${run.created} new, ${run.skipped} skipped`;
  return <p className="text-sm text-[var(--dp-ink-2)]" data-testid="import-auto-sync-line">{text}</p>;
}

function SourceRow({ s, onSync }) {
  const [busy, setBusy] = useState(false);
  const sync = async () => { setBusy(true); await onSync(s); setBusy(false); };
  return (
    <li className="flex flex-wrap items-center justify-between gap-2 border-t border-[var(--dp-line)] py-2 text-sm first:border-t-0" data-testid={`import-source-${s.key}`}>
      <span><b>{s.name}</b> <span className="text-[var(--dp-ink-3)]">· {s.kind === "sheet" ? "Google Sheet, checked every 30 s" : "CSV"} · {s.imported_count} rows seen</span>
        {s.last_line && <span className="block text-xs text-[var(--dp-ink-2)]" data-testid={`import-source-line-${s.key}`}>{s.last_line}</span>}</span>
      <Button variant="outline" onClick={sync} disabled={busy} className="h-9 px-3" data-testid={`import-sync-${s.key}`}>
        <RefreshCw className={`mr-1.5 h-4 w-4 ${busy ? "animate-spin" : ""}`} />Sync now
      </Button>
    </li>
  );
}

export function ImportJobs({ onImported }) {
  const [open, setOpen] = useState(false);
  const [info, setInfo] = useState(null);
  const [url, setUrl] = useState("");
  const [draft, setDraft] = useState(null);
  const [mapping, setMapping] = useState({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [line, setLine] = useState("");
  const file = useRef(null);

  const loadSources = () => http.get("/import/sources").then(({ data }) => setInfo(data)).catch(() => {});
  useEffect(() => {
    if (!open) return undefined;
    loadSources(); setError(""); setLine("");
    const t = setInterval(loadSources, 10000);
    return () => clearInterval(t);
  }, [open]);

  const start = async (req) => {
    setBusy(true); setError(""); setLine("");
    try {
      const { data } = await req();
      setDraft(data); setMapping(data.mapping || {});
    } catch (err) {
      setError(friendlyMessage(err, READ_FAIL));
    } finally { setBusy(false); }
  };
  const loadSheet = () => start(() => http.post("/import/sheet", { url }, { timeout: 60000 }));
  const upload = (f) => {
    if (!f) return;
    const form = new FormData();
    form.append("file", f);
    start(() => http.post("/import/csv", form, { timeout: 60000 }));
  };
  const confirm = async () => {
    setBusy(true); setError("");
    try {
      const { data } = await http.post(`/import/${draft.key}/confirm`, { mapping }, { timeout: 60000 });
      setLine(data.line); setDraft(null); loadSources(); onImported();
    } catch (err) {
      setError(friendlyMessage(err, READ_FAIL));
    } finally { setBusy(false); }
  };
  const sync = async (s) => {
    try {
      const { data } = await http.post(`/import/${s.key}/sync`, {}, { timeout: 60000 });
      setLine(data.line); loadSources(); onImported();
    } catch (err) { toast.error(friendlyMessage(err, READ_FAIL)); }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="h-10 px-4 font-semibold" data-testid="inbox-import-button"><FileSpreadsheet className="mr-2 h-4 w-4" />Import jobs</Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl bg-[var(--dp-surface)]" data-testid="import-dialog">
        <DialogHeader>
          <DialogTitle>Import jobs</DialogTitle>
          <DialogDescription>Each row becomes an Inbox request, read and priced like an email.</DialogDescription>
        </DialogHeader>
        {!draft && (
          <Tabs defaultValue="sheet">
            <TabsList><TabsTrigger value="sheet" data-testid="import-tab-sheet">Google Sheet</TabsTrigger><TabsTrigger value="csv" data-testid="import-tab-csv">CSV file</TabsTrigger></TabsList>
            <TabsContent value="sheet" className="space-y-2">
              {info && !info.google && <p className="text-sm text-[var(--dp-amber)]" data-testid="import-google-needed">Sign in with Google in Settings to read your sheets.</p>}
              <div className="flex gap-2">
                <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="Paste the Google Sheet link" data-testid="import-sheet-url"
                  className="h-10 min-w-0 flex-1 border border-[var(--dp-ink)] bg-[var(--dp-surface)] px-3 text-sm outline-none" />
                <Button onClick={loadSheet} disabled={busy || !url.trim()} className="h-10 px-4" data-testid="import-sheet-load">{busy ? "Reading..." : "Load sheet"}</Button>
              </div>
            </TabsContent>
            <TabsContent value="csv" className="space-y-2">
              <input ref={file} type="file" accept=".csv,text/csv" className="hidden" onChange={(e) => upload(e.target.files?.[0])} data-testid="import-csv-input" />
              <Button variant="outline" onClick={() => file.current?.click()} disabled={busy} className="h-10 px-4" data-testid="import-csv-button">
                <Upload className="mr-2 h-4 w-4" />{busy ? "Reading..." : "Choose a CSV file"}
              </Button>
            </TabsContent>
          </Tabs>
        )}
        {draft && <MatchTable draft={draft} mapping={mapping} setMapping={setMapping} />}
        {draft && (
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setDraft(null)} disabled={busy} data-testid="import-cancel">Back</Button>
            <Button onClick={confirm} disabled={busy} data-testid="import-confirm">{busy ? "Importing..." : `Import ${draft.row_count} rows`}</Button>
          </div>
        )}
        {error && <p className="text-sm text-[var(--dp-amber)]" role="alert" data-testid="import-error">{error}</p>}
        {line && <p className="text-sm font-medium" data-testid="import-result">{line}</p>}
        {info && <AutoSyncLine info={info} />}
        {info?.sources?.length > 0 && <ul className="border-t border-[var(--dp-ink)] pt-2" data-testid="import-sources">{info.sources.map((s) => <SourceRow key={s.key} s={s} onSync={sync} />)}</ul>}
      </DialogContent>
    </Dialog>
  );
}
