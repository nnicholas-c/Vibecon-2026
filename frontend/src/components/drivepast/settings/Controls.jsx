import { useState } from "react";
import { RotateCcw } from "lucide-react";
import { toast } from "sonner";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
  AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { http, friendlyMessage } from "@/lib/api";
import { useFleet } from "@/context/FleetContext";
import { Section } from "./Fields";

const LATER = [
  { key: "refresh-osm", label: "Refresh from OpenStreetMap" },
];
const LIVE = [
  { key: "send-request-1", label: "Send request 1 from the customer phone", path: "/demo/send-request-1", ok: "Request 1 arrived from the customer phone." },
  { key: "customer-accept", label: "Customer taps Accept", path: "/demo/customer-accept", ok: "The customer accepted the open quote." },
];

function LiveControl({ c, onReset }) {
  const { setHighlight, setPhonesOpen } = useFleet();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const run = async () => {
    setBusy(true);
    try {
      const { data } = await http.post(c.path, {}, { timeout: 90000 });
      if (data.booking) setHighlight(data.booking.stop_keys);
      setMsg({ ok: true, text: c.ok });
      await onReset();
      setPhonesOpen(true);
    } catch (err) {
      setMsg({ ok: false, text: friendlyMessage(err, "That didn't work. Try again.") });
    } finally {
      setBusy(false);
    }
  };
  return (
    <div>
      <Button variant="outline" onClick={run} disabled={busy} className="h-11 w-full justify-start rounded-lg" data-testid={`demo-control-${c.key}-button`}>
        {busy ? "Working..." : c.label}
      </Button>
      {msg && <p className={`mt-1 pl-1 text-xs ${msg.ok ? "text-[var(--dp-green)]" : "text-[var(--dp-amber)]"}`} data-testid={`demo-control-${c.key}-status`}>{msg.text}</p>}
    </div>
  );
}

export function Connections({ rows }) {
  return (
    <Section title="Connection status" note="What's live and what's using a built-in fallback." testId="settings-connections">
      <ul className="divide-y divide-[var(--dp-line)]">
        {rows.map((r) => (
          <li key={r.key} className="flex flex-wrap items-center justify-between gap-2 py-3" data-testid={`connection-row-${r.key}`}>
            <span className="min-w-0">
              <span className="block text-sm font-medium" data-testid={`connection-name-${r.key}`}>{r.name}</span>
              <span className="block text-xs text-[var(--dp-ink-2)]" data-testid={`connection-detail-${r.key}`}>{r.detail}</span>
            </span>
            <span
              data-testid={`connection-status-${r.key}`}
              className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                r.status === "connected" ? "bg-[var(--dp-green-soft)] text-[var(--dp-green)]" : "bg-[var(--dp-bg)] text-[var(--dp-ink-2)]"
              }`}
            >
              {r.label}
            </span>
          </li>
        ))}
      </ul>
    </Section>
  );
}

export function DemoControls({ onReset }) {
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState(null);
  const reset = async () => {
    setBusy(true);
    setStatus(null);
    try {
      await http.post("/demo/reset", {}, { timeout: 30000 });
      await onReset();
      setStatus({ ok: true, text: "Demo data reset" });
      toast.success("Demo data reset");
    } catch {
      setStatus({ ok: false, text: "Reset didn't finish. Try again." });
      toast.error("Reset didn't finish. Try again.");
    } finally {
      setBusy(false);
    }
  };
  return (
    <Section title="Demo controls" note="Tools for running the demo." testId="settings-demo-controls">
      <div className="space-y-3">
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button variant="outline" className="h-11 w-full justify-start rounded-lg" disabled={busy} data-testid="reset-demo-data-button">
              <RotateCcw className={`mr-2 h-4 w-4 ${busy ? "animate-spin" : ""}`} />
              {busy ? "Resetting..." : "Reset demo data"}
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent data-testid="reset-demo-confirm-dialog">
            <AlertDialogHeader>
              <AlertDialogTitle data-testid="reset-demo-confirm-title">Reset all demo data? This can't be undone.</AlertDialogTitle>
              <AlertDialogDescription>
                The fleet, routes, requests, chats and Settings go back to the start. Your team numbers stay.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel data-testid="reset-demo-cancel-button">Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={reset} data-testid="reset-demo-confirm-button">Reset demo data</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
        {status && (
          <p className={`text-sm font-medium ${status.ok ? "text-[var(--dp-green)]" : "text-[var(--dp-amber)]"}`} data-testid="reset-demo-status" role="status">
            {status.text}
          </p>
        )}
        {LIVE.map((c) => <LiveControl key={c.key} c={c} onReset={onReset} />)}
        {LATER.map((c) => (
          <div key={c.key}>
            <Button variant="outline" disabled className="h-11 w-full justify-start rounded-lg" data-testid={`demo-control-${c.key}-button`}>
              {c.label}
            </Button>
            <p className="mt-1 pl-1 text-xs text-[var(--dp-ink-3)]" data-testid={`demo-control-${c.key}-hint`}>Not built yet</p>
          </div>
        ))}
      </div>
    </Section>
  );
}
