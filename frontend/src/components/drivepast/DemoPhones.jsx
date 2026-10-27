import { useEffect, useRef, useState } from "react";
import { Check, Send, X } from "lucide-react";
import { toast } from "sonner";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { useFleet } from "@/context/FleetContext";
import { friendlyMessage, http } from "@/lib/api";

const PHONES = [["customer", "Customer"], ["driver", "Driver"], ["owner", "Owner"]];
const TYPING_MS = 900;

function stamp(at) {
  return new Date(at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function QuoteBubble({ m, onAct, busy, countdown }) {
  const open = m.quote_status === "sent";
  return (
    <div className="dp-sign space-y-2">
      <p>{m.text}</p>
      {open ? (
        <div className="flex gap-2">
          <button disabled={busy} onClick={() => onAct(m.quote_key, "accept")} data-testid="customer-quote-accept-button"
            className={`flex flex-1 items-center justify-center gap-1 rounded-full bg-[var(--dp-accent)] px-3 py-1.5 text-xs font-bold text-[#111214] transition-transform active:scale-95 ${countdown === 0 ? "scale-95" : ""}`}>
            <Check className="h-3.5 w-3.5" />{countdown != null ? `Accept in ${countdown}s` : "Accept"}
          </button>
          <button disabled={busy} onClick={() => onAct(m.quote_key, "decline")} data-testid="customer-quote-decline-button"
            className="flex flex-1 items-center justify-center gap-1 rounded-full border border-[var(--dp-line)] px-3 py-1.5 text-xs font-semibold transition-transform active:scale-95"><X className="h-3.5 w-3.5" />Decline</button>
        </div>
      ) : (
        <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--dp-ink-3)]" data-testid="customer-quote-status">{m.quote_status}</p>
      )}
    </div>
  );
}

export function Phone({ id, title, messages, onAct, onReply, busy, countdown, height = "h-[600px]" }) {
  const [text, setText] = useState("");
  const [shown, setShown] = useState(messages.length);
  const [typing, setTyping] = useState(false);
  const end = useRef(null);
  useEffect(() => {
    if (messages.length <= shown) { setShown(messages.length); return undefined; }
    const incoming = !messages[messages.length - 1].from_me;
    if (!incoming) { setShown(messages.length); return undefined; }
    setTyping(true);
    const t = setTimeout(() => { setTyping(false); setShown(messages.length); }, TYPING_MS);
    return () => clearTimeout(t);
  }, [messages, shown]);
  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [shown, typing]);
  const submit = (e) => { e.preventDefault(); if (text.trim()) { onReply(id, text.trim()); setText(""); } };
  return (
    <div className={`mx-auto flex ${height} w-full max-w-[300px] flex-col overflow-hidden border border-[var(--dp-ink)] bg-[var(--dp-surface)]`} data-testid={`phone-${id}`}>
      <div className="flex justify-center pt-2"><span className="h-5 w-24 bg-[var(--dp-line)]" /></div>
      <div className="border-b border-[var(--dp-line)] px-4 py-2 text-center">
        <p className="text-sm font-semibold">{title}</p>
        <p className="text-[11px] text-[var(--dp-ink-3)]">Demo phone · texting is off</p>
      </div>
      <div className="dp-scroll flex-1 space-y-2 overflow-y-auto px-3 py-3" data-testid={`phone-${id}-messages`}>
        {messages.slice(0, shown).map((m) => (
          <div key={m.key} className={`flex ${m.from_me ? "justify-end" : "justify-start"} dp-rise`}>
            <div className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${m.from_me ? "rounded-br-md bg-[var(--dp-accent)] text-[#111214]" : "rounded-bl-md bg-[var(--dp-card)]"}`} data-testid={`phone-${id}-message`}>
              {m.kind === "quote" ? <QuoteBubble m={m} onAct={onAct} busy={busy} countdown={countdown} /> : <p className="whitespace-pre-wrap break-words">{m.text}</p>}
              <p className={`tnum mt-1 text-[10px] ${m.from_me ? "text-[#111214]/70" : "text-[var(--dp-ink-3)]"}`}>{stamp(m.at)}</p>
            </div>
          </div>
        ))}
        {typing && (
          <div className="flex" data-testid={`phone-${id}-typing`}>
            <span className="flex gap-1 rounded-2xl bg-[var(--dp-card)] px-3 py-3">
              {[0, 1, 2].map((i) => <span key={i} className="dp-typing-dot h-1.5 w-1.5 rounded-full bg-[var(--dp-ink-2)]" style={{ animationDelay: `${i * 120}ms` }} />)}
            </span>
          </div>
        )}
        <div ref={end} />
      </div>
      <form onSubmit={submit} className="flex gap-2 border-t border-[var(--dp-line)] p-2">
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Message" aria-label={`${title} reply`} data-testid={`phone-${id}-input`}
          className="min-w-0 flex-1 rounded-full bg-[var(--dp-card)] px-3 py-2 text-sm outline-none" />
        <button type="submit" disabled={!text.trim() || busy} aria-label="Send" data-testid={`phone-${id}-send-button`}
          className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--dp-accent)] text-[#111214] disabled:opacity-40"><Send className="h-4 w-4" /></button>
      </form>
    </div>
  );
}

export function usePhones(active) {
  const { reload, setHighlight } = useFleet();
  const [data, setData] = useState({ customer: [], driver: [], owner: [] });
  const [busy, setBusy] = useState(false);
  const sig = useRef("");
  const load = async () => {
    try {
      const { data: d } = await http.get("/phones");
      setData(d);
      const s = ["customer", "driver", "owner"].map((p) => (d[p] || []).length).join("-");
      if (sig.current && s !== sig.current) reload();
      sig.current = s;
    } catch { /* next poll retries */ }
  };
  useEffect(() => {
    if (!active) return undefined;
    load();
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, [active]);

  const afterBooking = (res) => { if (res?.booking) setHighlight(res.booking.stop_keys, 60000); reload(); };
  const act = async (quoteKey, what) => {
    setBusy(true);
    try {
      const { data: res } = await http.post(`/quotes/${quoteKey}/${what}`, {}, { timeout: 30000 });
      afterBooking(res);
    } catch (err) {
      toast.error(friendlyMessage(err, "That didn't go through. Try again."));
    } finally {
      setBusy(false);
      load();
    }
  };
  const reply = async (phone, text) => {
    setBusy(true);
    try {
      const { data: res } = await http.post(`/phones/${phone}/messages`, { text }, { timeout: 90000 });
      afterBooking(res);
    } catch (err) {
      toast.error(friendlyMessage(err, "That didn't go through. Try again."));
    } finally {
      setBusy(false);
      load();
    }
  };
  return { data, busy, act, reply };
}

// Phone-shaped frame with Driver and Customer tabs; both are iframes of the no-login mobile pages.
function PhoneFrame({ active }) {
  const [tab, setTab] = useState("customer");
  const [van, setVan] = useState("van-1");
  const [reqKey, setReqKey] = useState(null);
  useEffect(() => {
    if (!active) return undefined;
    const pick = async () => {
      try {
        const [{ data: lv }, { data: ib }] = await Promise.all([http.get("/live"), http.get("/inbox")]);
        setVan(lv.last_booking?.unit_key || "van-1");
        const hit = [...ib.requests].reverse().find((r) => ["quoted", "booked"].includes(r.status));
        setReqKey(hit ? hit.key : null);
      } catch { /* next tick retries */ }
    };
    pick();
    const t = setInterval(pick, 5000);
    return () => clearInterval(t);
  }, [active]);
  const src = tab === "driver" ? `/driver/${van}` : reqKey ? `/customer/${reqKey}` : null;
  return (
    <div className="mx-auto mt-4 w-[399px] max-w-full" data-testid="phone-frame">
      <div className="mb-3 flex justify-center gap-1" role="tablist">
        {[["customer", "Customer"], ["driver", "Driver"]].map(([id, label]) => (
          <button key={id} type="button" role="tab" aria-selected={tab === id} onClick={() => setTab(id)}
            className={`h-9 px-4 text-sm font-semibold ${tab === id ? "bg-[var(--dp-ink)] text-[var(--dp-page)]" : "border border-[var(--dp-ink)]"}`} data-testid={`phone-tab-${id}`}>{label}</button>
        ))}
      </div>
      <div className="rounded-[40px] border-[12px] border-[var(--dp-ink)] bg-[var(--dp-ink)] shadow-xl">
        <div className="h-[700px] w-full overflow-hidden rounded-[28px] bg-[var(--dp-page)]">
          {src ? <iframe key={src} src={src} title={`${tab} phone`} className="h-full w-full border-0" data-testid={`phone-iframe-${tab}`} />
            : <p className="p-6 text-sm text-[var(--dp-ink-2)]" data-testid="phone-empty">No quoted or booked request yet.</p>}
        </div>
      </div>
    </div>
  );
}

export function DemoPhones() {
  const { phonesOpen, setPhonesOpen } = useFleet();

  return (
    <Sheet open={phonesOpen} onOpenChange={setPhonesOpen}>
      <SheetContent side="right" className="w-full overflow-y-auto border-[var(--dp-line)] bg-[var(--dp-page)] sm:max-w-[460px]" data-testid="demo-phones-drawer">
        <SheetHeader>
          <SheetTitle>Phones</SheetTitle>
          <SheetDescription className="text-[var(--dp-ink-2)]">What the driver and the customer see. Real texting is off.</SheetDescription>
        </SheetHeader>
        <PhoneFrame active={phonesOpen} />
      </SheetContent>
    </Sheet>
  );
}
