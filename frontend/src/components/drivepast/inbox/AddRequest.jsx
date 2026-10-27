import { useRef, useState } from "react";
import { FileUp, ImageUp, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { friendlyMessage, http } from "@/lib/api";

const SOURCES = [["email", "Email"], ["text", "Text"], ["voicemail", "Voicemail"]];

function UploadButton({ kind, accept, icon: Icon, label, busy, onFile }) {
  const ref = useRef(null);
  return (
    <>
      <input ref={ref} type="file" accept={accept} className="hidden" data-testid={`add-request-${kind}-input`}
        onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; if (f) onFile(kind, f); }} />
      <button type="button" disabled={busy} onClick={() => ref.current?.click()} data-testid={`add-request-${kind}-button`}
        className="flex flex-1 items-center justify-center gap-2 rounded-2xl border border-dashed border-[var(--dp-line)] px-4 py-4 text-sm font-medium transition-colors hover:bg-[var(--dp-bg)] disabled:opacity-50">
        <Icon className="h-4 w-4" /> {label}
      </button>
    </>
  );
}

export function AddRequest({ onAdded }) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [source, setSource] = useState("email");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  const done = (data) => {
    setOpen(false);
    setText("");
    onAdded(data);
  };

  const submit = async () => {
    if (!text.trim()) { setError("Paste the request text first."); return; }
    setBusy("Reading the request...");
    setError("");
    try {
      const { data } = await http.post("/inbox", { text, source }, { timeout: 90000 });
      done(data);
    } catch (err) {
      setError(friendlyMessage(err, "Couldn't read that right now. Try again."));
    } finally {
      setBusy("");
    }
  };

  const upload = async (kind, file) => {
    setBusy(kind === "pdf" ? "Reading the PDF..." : "Reading the photo...");
    setError("");
    const form = new FormData();
    form.append("file", file);
    form.append("kind", kind);
    try {
      const { data } = await http.post("/inbox/upload", form, { timeout: 90000 });
      done(data);
    } catch (err) {
      setError(friendlyMessage(err, "Couldn't read that right now. Try again."));
    } finally {
      setBusy("");
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { setOpen(v); setError(""); }}>
      <DialogTrigger asChild>
        <Button variant="outline" className="h-10 rounded-full px-4 font-semibold" data-testid="inbox-add-request-button">
          <Plus className="mr-2 h-4 w-4" /> Add a request
        </Button>
      </DialogTrigger>
      <DialogContent className="border-[var(--dp-line)] bg-[var(--dp-card)] sm:max-w-lg" data-testid="add-request-dialog">
        <DialogHeader>
          <DialogTitle>Add a request</DialogTitle>
          <DialogDescription className="text-[var(--dp-ink-2)]">Paste an email, text or voicemail, or upload a PDF or photo.</DialogDescription>
        </DialogHeader>
        <div className="flex gap-1 rounded-full bg-[var(--dp-bg)] p-1" role="radiogroup">
          {SOURCES.map(([k, label]) => (
            <button key={k} role="radio" aria-checked={source === k} onClick={() => setSource(k)} data-testid={`add-request-source-${k}`}
              className={`flex-1 rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${source === k ? "bg-[var(--dp-ink)] text-[var(--dp-page)]" : "text-[var(--dp-ink-2)]"}`}>
              {label}
            </button>
          ))}
        </div>
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={6} placeholder="Paste the request here"
          className="w-full rounded-2xl border border-[var(--dp-line)] bg-[var(--dp-surface)] p-3 text-sm outline-none focus:border-[var(--dp-green)]"
          data-testid="add-request-text-input" />
        <Button onClick={submit} disabled={Boolean(busy)} className="h-11 rounded-full font-semibold" data-testid="add-request-submit-button">
          {busy || "Read this request"}
        </Button>
        <div className="flex gap-2">
          <UploadButton kind="pdf" accept="application/pdf" icon={FileUp} label="Upload a PDF" busy={Boolean(busy)} onFile={upload} />
          <UploadButton kind="photo" accept="image/jpeg,image/png,image/webp" icon={ImageUp} label="Upload a photo" busy={Boolean(busy)} onFile={upload} />
        </div>
        {error && <p className="text-sm text-[var(--dp-amber)]" role="alert" data-testid="add-request-error">{error}</p>}
      </DialogContent>
    </Dialog>
  );
}
