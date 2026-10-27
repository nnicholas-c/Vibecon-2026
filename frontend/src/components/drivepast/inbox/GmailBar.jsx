import { useEffect, useState } from "react";
import { http } from "@/lib/api";

// Gmail connection status only; the backend polls Gmail every 10 s by itself.
export function GmailBar() {
  const [st, setSt] = useState(null);
  useEffect(() => { http.get("/google/status").then(({ data }) => setSt(data)).catch(() => setSt(null)); }, []);
  if (!st || (!st.connected && !st.expired)) return null;
  return (
    <div className="dp-card space-y-2 px-4 py-3" data-testid="gmail-bar">
      {st.expired ? (
        <p className="text-sm font-medium text-[var(--dp-amber)]" data-testid="gmail-expired">Google connection expired. Sign in with Google again.</p>
      ) : (
        <p className="text-sm text-[var(--dp-ink-2)]" data-testid="gmail-line">{st.line} New emails get read and priced on their own.</p>
      )}
    </div>
  );
}
