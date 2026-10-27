import { createContext, useContext, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { http } from "@/lib/api";
import { openDemo } from "./openDemo";

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const DEMO_KEY = "dp-demo-open";
const TAGLINE = "Price every job from the van that already drives past.";
const AuthContext = createContext({ me: null, signOut: async () => {} });

export const useAuth = () => useContext(AuthContext);

function SignIn({ me, onDemo }) {
  const location = useLocation();
  const flag = new URLSearchParams(location.search).get("google");
  const [msg, setMsg] = useState(flag === "failed" ? "Google sign-in didn't finish. Try again or open the demo." : flag === "not_set" ? "Google sign-in isn't set up yet." : "");
  const google = () => {
    if (!me?.google_configured) return setMsg("Google sign-in isn't set up yet.");
    window.location.href = `${BACKEND}/api/auth/google/start?origin=signin`;
  };
  return (
    <div className="flex min-h-[100dvh] items-center justify-center bg-[var(--dp-page)] px-5 py-10" data-testid="signin-screen">
      <div className="dp-card dp-rise w-full max-w-md space-y-6 p-8">
        <div>
          <p className="font-display text-4xl font-bold tracking-tight" data-testid="signin-brand">Drivepast</p>
          <p className="mt-2 text-base text-[var(--dp-ink-2)]" data-testid="signin-tagline">{TAGLINE}</p>
        </div>
        <div className="flex flex-col gap-3">
          <button type="button" onClick={google} className="h-12 bg-[var(--dp-ink)] text-base font-bold text-[var(--dp-surface)]" data-testid="signin-google-button">
            Sign in with Google
          </button>
          <button type="button" onClick={onDemo} className="h-12 border border-[var(--dp-ink)] bg-[var(--dp-surface)] text-base font-semibold text-[var(--dp-ink)] transition-colors hover:bg-[var(--dp-page)]" data-testid="signin-demo-button">
            Open the demo
          </button>
        </div>
        {msg && <p className="rounded-xl bg-[var(--dp-amber-soft)] px-3 py-2 text-sm font-medium text-[var(--dp-amber)]" role="alert" data-testid="signin-message">{msg}</p>}
        <p className="text-xs text-[var(--dp-ink-3)]">You don't need an account for the demo. Sign in with Google only to get real requests from your Gmail.</p>
      </div>
    </div>
  );
}

export function AuthGate({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [me, setMe] = useState(null);
  const [demo, setDemo] = useState(() => localStorage.getItem(DEMO_KEY) === "1");
  useEffect(() => {
    http.get("/auth/me").then(({ data }) => setMe(data)).catch(() => setMe({ signed_in: false, google_configured: false }));
  }, []);
  const signOut = async () => {
    await http.post("/auth/logout").catch(() => {});
    localStorage.removeItem(DEMO_KEY);
    setDemo(false);
    setMe((m) => ({ ...m, signed_in: false, name: null, picture: null, email: null }));
    navigate("/signin");
  };
  if (!me) return <div className="min-h-[100dvh] bg-[var(--dp-page)]" data-testid="auth-loading" />;
  const inside = me.signed_in || demo;
  // REQ-1300: /signin always shows the login screen, even after an earlier demo.
  if (!inside || location.pathname === "/signin") return <SignIn me={me} onDemo={async () => { await openDemo(navigate); setDemo(true); }} />;
  return <AuthContext.Provider value={{ me, signOut }}>{children}</AuthContext.Provider>;
}
