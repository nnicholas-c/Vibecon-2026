import { useEffect, useRef, useState } from "react";
import { ArrowUp, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useFleet } from "@/context/FleetContext";
import { friendlyMessage, http } from "@/lib/api";
import { MorningBrief } from "./MorningBrief";

const TAGLINE = "Price every job from the van that already drives past.";

function Bubble({ turn, index }) {
  const mine = turn.role === "owner";
  return (
    <div className={`dp-rise flex ${mine ? "justify-end" : "justify-start"}`}>
      <div
        data-testid={`chat-message-${index}`}
        data-role={turn.role}
        className={`max-w-[85%] whitespace-pre-wrap break-words rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          mine ? "rounded-br-md bg-[var(--dp-ink)] text-[var(--dp-page)]" : "rounded-bl-md border border-[var(--dp-line)] bg-[var(--dp-surface)]"
        }`}
      >
        {turn.text}
        {(turn.tool_calls || []).filter((c) => c.name === "explain_stop" && c.label).map((c, j) => (
          <span key={j} className="mt-2 flex flex-wrap items-center gap-2 font-mono text-[11px] text-[var(--dp-ink-3)]" data-testid={`chat-tool-line-${index}-${j}`}>
            <span className={`rounded-none px-1.5 py-0.5 font-semibold uppercase tracking-wider ${c.label === "Not booked yet" ? "bg-[var(--dp-amber-soft)] text-[var(--dp-amber)]" : c.label === "Booked" ? "bg-[var(--dp-green-soft)] text-[var(--dp-green)]" : "bg-[var(--dp-bg)] text-[var(--dp-ink-2)]"}`} data-testid={`chat-tool-label-${index}-${j}`}>{c.label}</span>
            {c.stop_name && <span className="text-[var(--dp-ink-2)]" data-testid={`chat-tool-stop-${index}-${j}`}>{c.stop_name}</span>}
          </span>
        ))}
      </div>
    </div>
  );
}

function EmptyChat({ name }) {
  return (
    <div className="mt-10 px-2 text-center" data-testid="chat-empty-state">
      <span className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-[var(--dp-green-soft)] text-[var(--dp-green)]">
        <Sparkles className="h-5 w-5" />
      </span>
      <p className="mt-4 font-display text-base font-semibold">{TAGLINE}</p>
      <p className="mt-2 text-sm text-[var(--dp-ink-2)]">Ask {name} about today's vans, or tap a question below.</p>
    </div>
  );
}

function Composer({ prompts, onSend, sending, error, draft }) {
  const [text, setText] = useState(draft || "");
  const canSend = text.trim().length > 0 && !sending;
  const submit = async (value) => {
    const ok = await onSend(value);
    if (ok && value === text) setText("");
  };
  return (
    <div className="border-t border-[var(--dp-line)] bg-[var(--dp-surface)] p-3" data-testid="chat-composer">
      <div className="mb-2 flex flex-wrap gap-1.5">
        {prompts.map((p, i) => (
          <button
            key={p}
            disabled={sending}
            onClick={() => submit(p)}
            data-testid={`chat-suggested-prompt-${i}`}
            className="rounded-lg border border-[var(--dp-line)] bg-[var(--dp-surface)] px-3 py-1.5 text-left text-xs text-[var(--dp-ink-2)] transition-colors hover:border-[var(--dp-green)] hover:text-[var(--dp-green)] disabled:opacity-50"
          >
            {p}
          </button>
        ))}
      </div>
      {error && <p className="mb-2 text-xs text-[var(--dp-red)]" data-testid="chat-error" role="alert">{error}</p>}
      <form
        className="flex items-end gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (canSend) submit(text);
        }}
      >
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type a message"
          maxLength={2000}
          data-testid="chat-input"
          className="h-11 min-w-0 flex-1 rounded-lg border border-[var(--dp-line)] bg-[var(--dp-bg)] px-4 text-sm outline-none transition-colors focus:border-[var(--dp-green)] focus:bg-[var(--dp-surface)]"
        />
        <Button type="submit" disabled={!canSend} size="icon" className="h-11 w-11 shrink-0 rounded-full" data-testid="chat-send-button" aria-label="Send">
          <ArrowUp className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
}

export default function ChatPane({ agentKey, draft, draftId }) {
  const { version } = useFleet();
  const [thread, setThread] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    let live = true;
    setThread(null);
    setSendError("");
    http.get(`/agents/${agentKey}/thread`)
      .then(({ data }) => live && (setThread(data), setLoadError("")))
      .catch((err) => live && setLoadError(friendlyMessage(err, "Couldn't load this chat. Try again in a moment.")));
    return () => { live = false; };
  }, [agentKey, version]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [thread?.turns?.length]);

  const send = async (text) => {
    if (!text.trim()) return false;
    setSending(true);
    setSendError("");
    try {
      const { data } = await http.post(`/agents/${agentKey}/messages`, { text });
      setThread(data);
      return data;
    } catch {
      setSendError("Couldn't send that. Try again.");
      return false;
    } finally {
      setSending(false);
    }
  };

  // The demo autoplay asks through this pane so the question and reply show where the presenter looks.
  const sendRef = useRef(send);
  sendRef.current = send;
  useEffect(() => {
    if (agentKey !== "dispatch") return undefined;
    const onAsk = async (e) => {
      const data = await sendRef.current(e.detail.text);
      const last = data ? [...(data.turns || [])].reverse().find((t) => t.role === "agent") : null;
      e.detail.done(last?.text || null);
    };
    window.addEventListener("dp-agent-ask", onAsk);
    return () => window.removeEventListener("dp-agent-ask", onAsk);
  }, [agentKey]);

  const agent = thread?.agent;
  const turns = thread?.turns || [];
  return (
    <div className="flex min-h-0 flex-1 flex-col" data-testid="chat-pane">
      <header className="flex items-center gap-3 border-b border-[var(--dp-line)] bg-[var(--dp-surface)] px-5 py-4">
        <span className="h-2.5 w-2.5 rounded-full" style={{ background: agent?.color || "var(--dp-green)" }} />
        <div className="min-w-0">
          <p className="font-display text-sm font-semibold" data-testid="chat-agent-name">{agent ? `${agent.name} agent` : "Loading chat"}</p>
          <p className="text-xs text-[var(--dp-ink-3)]">Answers come from today's routes and prices.</p>
        </div>
      </header>
      <div className="dp-scroll min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-5" data-testid="chat-messages">
        {agentKey === "dispatch" && <MorningBrief />}
        {loadError && <p className="text-center text-sm text-[var(--dp-ink-2)]" data-testid="chat-load-error">{loadError}</p>}
        {agent && turns.length === 0 && <EmptyChat name={agent.name} />}
        {turns.map((t, i) => <Bubble key={`${i}-${t.at}`} turn={t} index={i} />)}
        <div ref={endRef} />
      </div>
      <Composer key={`${agentKey}-${draftId || ""}`} draft={draft} prompts={agent?.suggested_prompts || []} onSend={send} sending={sending || !agent} error={sendError} />
    </div>
  );
}
