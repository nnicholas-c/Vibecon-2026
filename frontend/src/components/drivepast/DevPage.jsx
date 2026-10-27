import { useState } from "react";
import { Link } from "react-router-dom";
import { friendlyMessage, http } from "@/lib/api";

// Not linked in the nav: the stage backup emails.
export default function DevPage() {
  const [busy, setBusy] = useState(false);
  const [line, setLine] = useState("");
  const fire = async (path, ok) => {
    setBusy(true); setLine("");
    try {
      const { data } = await http.post(path, {}, { timeout: 30000 });
      setLine(data.ok ? `${ok} (${data.request_key}). Watch the Inbox.` : "That email was already in the inbox.");
    } catch (err) {
      setLine(friendlyMessage(err, "The demo email didn't go in. Try again."));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="min-h-[100dvh] bg-[var(--dp-page)] px-6 py-10 text-[var(--dp-ink)]" data-testid="dev-page">
      <div className="mx-auto max-w-xl space-y-8">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-wider text-[var(--dp-ink-3)]">Presenter tools</p>
          <h1 className="font-display text-4xl font-bold">/dev</h1>
          <Link to="/dispatch" className="text-sm underline" data-testid="dev-dispatch-link">Open Fleet</Link>
        </div>
        <section className="dp-card space-y-3 p-5">
          <h2 className="text-base font-semibold">Fire demo email</h2>
          <p className="text-sm text-[var(--dp-ink-2)]">Use this if the live email is slow on stage. It comes in as a Gmail request for Grand Ave. The quote and the confirmation go to the Customer demo phone.</p>
          <button type="button" onClick={() => fire("/demo/fire-email", "Sent as Gmail from dana@grandlakeoptometry.example")} disabled={busy} className="h-11 bg-[var(--dp-ink)] px-5 text-sm font-bold text-[var(--dp-page)] disabled:opacity-50" data-testid="dev-fire-email-button">
            {busy ? "Sending…" : "Fire demo email"}
          </button>
          {line && <p className="text-sm" role="status" data-testid="dev-fire-email-result">{line}</p>}
        </section>
        <section className="dp-card space-y-3 p-5">
          <h2 className="text-base font-semibold">Fire tricky email</h2>
          <p className="text-sm text-[var(--dp-ink-2)]">Lakeshore Dental asks for a 5pm pickup, but the office closes at 4:30. It comes in as a Gmail request and should show amber "Needs clarification" with 4:15pm offered. Nothing gets emailed.</p>
          <button type="button" onClick={() => fire("/demo/fire-tricky-email", "Sent as Gmail from frontdesk@lakeshoredental.example")} disabled={busy} className="h-11 border border-[var(--dp-ink)] px-5 text-sm font-bold disabled:opacity-50" data-testid="dev-fire-tricky-email-button">
            {busy ? "Sending…" : "Fire tricky email"}
          </button>
        </section>
      </div>
    </div>
  );
}
