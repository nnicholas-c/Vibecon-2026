import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { friendlyMessage, http } from "@/lib/api";
import { Section } from "./Fields";

const BACKEND = process.env.REACT_APP_BACKEND_URL;

export function EmailGoogle() {
  const location = useLocation();
  const navigate = useNavigate();
  const [st, setSt] = useState(null);
  const [busy, setBusy] = useState(false);
  const flag = new URLSearchParams(location.search).get("google");
  const load = () => http.get("/google/status").then(({ data }) => setSt(data)).catch(() => setSt(null));
  useEffect(() => { load(); }, []);
  const disconnect = async () => {
    setBusy(true);
    try { setSt((await http.post("/google/disconnect")).data); navigate("/settings", { replace: true }); }
    catch (err) { toast.error(friendlyMessage(err, "Couldn't disconnect. Try again.")); }
    finally { setBusy(false); }
  };
  if (!st) return null;
  const failed = flag === "failed" && !st.connected;
  return (
    <Section title="Email and Google" note="Connect Gmail to get real requests by email. Seeded requests still use the Demo phones." testId="settings-email-google">
      <div className="space-y-3">
        <p className="text-sm font-semibold" data-testid="google-status">{st.expired ? st.message : st.connected ? `Connected as ${st.email}` : st.configured ? "Not connected" : st.message}</p>
        {failed && <p className="rounded-xl bg-[var(--dp-amber-soft)] px-3 py-2 text-sm font-medium text-[var(--dp-amber)]" role="alert" data-testid="google-failed">Google sign-in didn't finish. Nothing was connected.</p>}
        {flag === "not_set" && <p className="text-sm text-[var(--dp-amber)]" data-testid="google-not-set">Google sign-in isn't set up yet.</p>}
        {st.connected && st.missing.map((m) => <p key={m} className="text-sm text-[var(--dp-amber)]" data-testid="google-missing">{m}</p>)}
        {st.connected && st.sheets_allowed && <p className="text-sm text-[var(--dp-ink-2)]" data-testid="google-sheets-allowed">Google Sheets: allowed</p>}
        {st.connected && st.line && <p className="text-sm text-[var(--dp-ink-2)]" data-testid="google-line">{st.line}</p>}
        <div className="flex flex-wrap gap-2">
          {(!st.connected || st.expired) && (
            <Button asChild={st.configured} disabled={!st.configured} className="h-10 rounded-full px-5 font-semibold" data-testid="google-sign-in-button">
              {st.configured ? <a href={`${BACKEND}/api/auth/google/start?origin=settings`}>Sign in with Google</a> : <span>Sign in with Google</span>}
            </Button>
          )}
          {(st.connected || st.expired) && (
            <Button variant="outline" onClick={disconnect} disabled={busy} className="h-10 rounded-full px-5" data-testid="google-disconnect-button">{busy ? "Disconnecting..." : "Disconnect"}</Button>
          )}
        </div>
      </div>
    </Section>
  );
}
