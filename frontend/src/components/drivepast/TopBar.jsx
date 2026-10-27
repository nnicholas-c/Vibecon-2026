import { useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, Search, Smartphone } from "lucide-react";
import { useFleet } from "@/context/FleetContext";
import { http } from "@/lib/api";
import { useAuth } from "./AuthGate";

async function buildIndex() {
  const [m, r] = await Promise.all([http.get("/map/fleet"), http.get("/inbox")]);
  const out = [];
  m.data.units.forEach((u) => {
    out.push({ kind: "Van", text: `${u.name} ${u.nickname}`, label: u.name, sub: u.nickname, to: `/units/${u.unit_key}` });
    u.stops.forEach((s) => out.push({ kind: "Stop", text: `${s.name} ${s.address}`, label: s.name, sub: `${u.name} · ${s.arrival_label}`, to: `/units/${u.unit_key}` }));
  });
  r.data.requests.forEach((q) => out.push({ kind: "Request", text: `${q.sender} ${q.summary} ${q.number}`, label: q.sender, sub: q.status_label, to: `/inbox/${q.key}` }));
  return out;
}

function SearchBox() {
  const navigate = useNavigate();
  const { version } = useFleet();
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const idx = useRef({ v: -1, rows: [] });
  const [rows, setRows] = useState([]);
  const load = async () => {
    if (idx.current.v === version) return;
    idx.current = { v: version, rows: await buildIndex() };
    setRows(idx.current.rows);
  };
  const hits = useMemo(() => {
    const t = q.trim().toLowerCase();
    return t ? rows.filter((r) => r.text.toLowerCase().includes(t)).slice(0, 8) : [];
  }, [q, rows]);
  const go = (h) => { navigate(h.to); setQ(""); setOpen(false); };
  return (
    <div className="relative min-w-[200px] flex-1 md:max-w-[340px]">
      <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--dp-ink-3)]" />
      <input value={q} onChange={(e) => { setQ(e.target.value); setOpen(true); }} onFocus={() => { load(); setOpen(true); }}
        onBlur={() => setTimeout(() => setOpen(false), 150)} onKeyDown={(e) => { if (e.key === "Enter" && hits[0]) go(hits[0]); if (e.key === "Escape") setOpen(false); }}
        placeholder="Search vans, stops or requests…" aria-label="Search vans, stops or requests" className="dp-search" data-testid="topbar-search-input" />
      {open && hits.length > 0 && (
        <div className="dp-search-menu" data-testid="topbar-search-results">
          {hits.map((h, i) => (
            <button key={`${h.to}-${i}`} type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => go(h)} className="dp-search-row" data-testid={`topbar-search-result-${i}`}>
              <span className="dp-search-kind">{h.kind}</span>
              <span className="min-w-0 flex-1 truncate">{h.label}<span className="text-[var(--dp-ink-3)]"> · {h.sub}</span></span>
            </button>
          ))}
        </div>
      )}
      {open && q.trim() && hits.length === 0 && rows.length > 0 && (
        <div className="dp-search-menu px-4 py-3 text-sm text-[var(--dp-ink-2)]" data-testid="topbar-search-empty">No van, stop or request matches that.</div>
      )}
    </div>
  );
}

export function TopBar() {
  const { fleet, setPhonesOpen } = useFleet();
  const { me, signOut } = useAuth();
  const navigate = useNavigate();
  const count = fleet?.inbox_new_count ?? 0;
  return (
    <header className="dp-topbar" data-testid="topbar">
      <div id="dp-topbar-chips" className="order-last min-w-0 basis-full min-[2200px]:order-none min-[2200px]:basis-auto" />
      <div className="ml-auto flex min-w-0 flex-1 items-center justify-end gap-2">
        <SearchBox />
        <button type="button" onClick={() => setPhonesOpen(true)} className="dp-icon-btn !w-auto gap-1.5 px-3 text-xs font-semibold" aria-label="Phones" data-testid="topbar-phones-button">
          <Smartphone className="h-4 w-4" /><span className="hidden 2xl:inline">Phones</span>
        </button>
        <button type="button" onClick={() => navigate("/inbox")} className="dp-icon-btn relative" aria-label={`Inbox, ${count} new`} data-testid="topbar-bell">
          <Bell className="h-4 w-4" />
          {count > 0 && <span className="dp-bell-count tnum" data-testid="topbar-bell-count">{count}</span>}
        </button>
        <div className="flex items-center gap-2 pl-1" data-testid="topbar-owner">
          {me?.signed_in ? (
            <>
              {me.picture ? <img src={me.picture} alt="" referrerPolicy="no-referrer" className="h-9 w-9 rounded-full object-cover" data-testid="topbar-user-picture" />
                : <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--dp-accent)] text-xs font-bold text-[#111214]">{(me.name || "?").slice(0, 1)}</span>}
              <span className="hidden whitespace-nowrap text-sm leading-tight lg:block" data-testid="topbar-user-name">{me.name}</span>
              <button type="button" onClick={signOut} className="dp-icon-btn !w-auto px-3 text-xs font-semibold" data-testid="topbar-sign-out">Sign out</button>
            </>
          ) : (
            <>
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--dp-accent)] text-xs font-bold text-[#111214]">RD</span>
          <span className="hidden whitespace-nowrap text-sm leading-tight lg:block">Rosa Delgado<span className="text-[var(--dp-ink-3)]"> · Owner</span></span>
          <button type="button" onClick={signOut} className="dp-icon-btn !w-auto px-3 text-xs font-semibold" data-testid="topbar-sign-out">Sign out</button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
