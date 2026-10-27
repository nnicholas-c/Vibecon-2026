import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { DEMO_KEY } from "@/landing/lib/constants";

export const inDemoSession = () => localStorage.getItem(DEMO_KEY) === "1";
export const onFleet = () => window.location.pathname === "/dispatch";

const ASK_DELAY_MS = 1200;
const REPLY_WAIT_MS = 10000;
const HOLD_AFTER_PHONES_MS = 6000;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Sends the question through the Fleet chat pane and resolves with the reply text, or null after 10 s (REQ-1406).
function askChat(text) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve(null), REPLY_WAIT_MS);
    window.dispatchEvent(new CustomEvent("dp-agent-ask", { detail: { text, done: (reply) => { clearTimeout(timer); resolve(reply); } } }));
  });
}

function DockedPhones({ phones, onClose }) {
  return (
    <div className="fixed bottom-2 left-[690px] top-[72px] z-40 flex gap-3 border border-[var(--dp-ink)] bg-[var(--dp-page)] p-3 shadow-xl dp-rise" data-testid="autoplay-phones">
      {[["driver", "Driver", `/driver/${phones.unitKey}`], ["customer", "Customer", `/customer/${phones.requestKey}`]].map(([id, title, src]) => (
        <div key={id} className="flex w-[330px] flex-col" data-testid={`autoplay-phone-${id}`}>
          <p className="mb-2 text-center text-sm font-semibold">{title}</p>
          <div className="min-h-0 flex-1 overflow-hidden rounded-[28px] border-[8px] border-[var(--dp-ink)] bg-[var(--dp-page)]">
            <iframe src={src} title={`${title} phone`} className="h-full w-full border-0" data-testid={`autoplay-iframe-${id}`} />
          </div>
        </div>
      ))}
      <button type="button" onClick={onClose} aria-label="Close phones" className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center border border-[var(--dp-ink)] bg-[var(--dp-surface)]" data-testid="autoplay-phones-close">
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

// REQ-1400 to 1412: after a booking pop-up in a demo session on Fleet, ask "why" in the chat, then open both phones. One at a time.
export function DemoAutoplay() {
  const queue = useRef([]);
  const busy = useRef(false);
  const [phones, setPhones] = useState(null);
  const [state, setState] = useState({ step: "idle" });

  useEffect(() => {
    const run = async () => {
      if (busy.current) return;
      busy.current = true;
      while (queue.current.length) {
        const b = queue.current.shift();
        const t0 = Date.now();
        const mark = (step, extra = {}) => setState((s) => ({ ...s, ...extra, step, [`${step}_ms`]: Date.now() - t0, request_key: b.request_key }));
        mark("popup");
        await sleep(ASK_DELAY_MS);
        mark("asked");
        const reply = await askChat(`Why did ${b.customer}'s job go on ${b.unit_name}?`);
        mark(reply ? "replied" : "reply_timeout");
        setPhones({ unitKey: b.unit_key, requestKey: b.request_key });
        mark("phones");
        await sleep(HOLD_AFTER_PHONES_MS);
        mark("done");
      }
      busy.current = false;
    };
    const onBooking = (e) => {
      if (!inDemoSession() || !onFleet() || !e.detail?.customer || !e.detail?.request_key) return;
      queue.current.push(e.detail);
      run();
    };
    window.addEventListener("dp-autoplay", onBooking);
    return () => window.removeEventListener("dp-autoplay", onBooking);
  }, []);

  return (
    <>
      <span hidden data-testid="autoplay-state" data-state={JSON.stringify(state)} />
      {phones && <DockedPhones phones={phones} onClose={() => setPhones(null)} />}
    </>
  );
}
