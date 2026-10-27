import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, Ban, ChevronDown, MapPin, Send, X } from "lucide-react";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
  AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { money } from "@/lib/format";

export function AiTag({ tag, testId }) {
  if (!tag) return null;
  const ours = tag === "our model" || tag.startsWith("OpenAI (your key)");
  return (
    <span data-testid={testId}
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${ours ? "bg-[var(--dp-accent)] text-[#111214]" : "bg-[var(--dp-bg)] text-[var(--dp-ink-2)]"}`}>
      {tag}
    </span>
  );
}

function Stat({ label, value, testId }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wider text-[var(--dp-ink-3)]">{label}</p>
      <p className="tnum text-sm font-semibold" data-testid={testId}>{value}</p>
    </div>
  );
}

function CardActions({ o, id, actions }) {
  const [ask, setAsk] = useState(false);
  const send = () => (o.loses_money ? setAsk(true) : actions.onSend(o, false));
  return (
    <div className="flex flex-wrap gap-2 pt-1">
      <button onClick={send} disabled={actions.busy} data-testid={`${id}-send-button`}
        className="inline-flex h-11 items-center gap-1.5 bg-[var(--dp-ink)] px-4 text-sm font-bold text-[var(--dp-surface)] disabled:opacity-50">
        <Send className="h-3.5 w-3.5" /> Send
      </button>
      <button onClick={() => actions.onReject(o)} disabled={actions.busy} data-testid={`${id}-reject-button`}
        className="inline-flex items-center gap-1.5 rounded-full border border-[var(--dp-line)] px-4 py-1.5 text-sm font-semibold transition-colors hover:bg-[var(--dp-bg)] disabled:opacity-50">
        <X className="h-3.5 w-3.5" /> Reject
      </button>
      <AlertDialog open={ask} onOpenChange={setAsk}>
        <AlertDialogContent data-testid={`${id}-loss-confirm`}>
          <AlertDialogHeader>
            <AlertDialogTitle>This loses money at your usual price. Send anyway?</AlertDialogTitle>
            <AlertDialogDescription>It costs {money(o.added_cost)} and the quote is {money(o.price)}.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid={`${id}-loss-cancel`}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => actions.onSend(o, true)} data-testid={`${id}-loss-send`}>Send anyway</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export function OptionCard({ o, id, compact, actions, tripLine }) {
  const navigate = useNavigate();
  return (
    <div className="dp-card dp-sheet dp-rise space-y-3 p-5" data-testid={`${id}`}>
      {o.labels.length > 0 && (
        <div className="flex flex-wrap gap-1.5" data-testid={`${id}-labels`}>
          <span className="rounded-full bg-[var(--dp-accent)] px-2.5 py-0.5 text-xs font-bold text-[#111214]" data-testid={`${id}-title`}>{o.title || o.labels.join(" + ")}</span>
        </div>
      )}
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="flex items-center gap-2 font-semibold">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: o.color }} />
            <span data-testid={`${id}-van`}>{o.unit_name}</span>
          </p>
          <p className="tnum mt-1 text-sm text-[var(--dp-ink-2)]" data-testid={`${id}-times`}>
            Pickup {o.pickup_label}{o.dropoff_label ? ` · drop-off ${o.dropoff_label}` : ""}
          </p>
        </div>
        <div className="text-right">
          <p className="font-display tnum text-2xl font-bold text-[var(--dp-green)]" data-testid={`${id}-price`}>{money(o.price)}</p>
          <p className="text-xs text-[var(--dp-ink-3)]">a {o.per}</p>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3 rounded-lg bg-[var(--dp-bg)] px-3 py-2.5">
        <Stat label="Added" value={`+${o.added_minutes} min`} testId={`${id}-minutes`} />
        <Stat label="Miles" value={`+${o.added_miles.toFixed(1)} mi`} testId={`${id}-miles`} />
        <Stat label="Cost" value={money(o.added_cost)} testId={`${id}-cost`} />
      </div>
      {o.monthly_total != null && <p className="tnum text-sm" data-testid={`${id}-monthly`}>{money(o.monthly_total)} a month</p>}
      {tripLine && <p className="text-xs text-[var(--dp-ink-3)]" data-testid={`${id}-new-trip`}>{tripLine}</p>}
      {o.market_line && <p className="text-sm text-[var(--dp-ink-2)]" data-testid={`${id}-market`}>{o.market_line}</p>}
      {o.reasons.map((r, i) => <p key={r} className="text-sm font-medium" data-testid={`${id}-reason-${i}`}>{r}</p>)}
      <p className="rounded-lg border-l-2 border-[var(--dp-accent)] bg-[var(--dp-surface)] px-3 py-2 text-sm" data-testid={`${id}-customer-line`}>
        <span className="block text-[11px] uppercase tracking-wider text-[var(--dp-ink-3)]">Customer sees</span>
        {o.customer_line}
      </p>
      {!compact && <p className="text-xs text-[var(--dp-ink-3)]" data-testid={`${id}-explanation`}>{o.explanation}</p>}
      {o.loses_money && (
        <p className="flex items-center gap-2 rounded-lg bg-[var(--dp-amber-soft)] px-3 py-2 text-sm font-medium text-[var(--dp-amber)]" data-testid={`${id}-loses-money`}>
          <AlertTriangle className="h-4 w-4 shrink-0" /> Loses money at your usual price. Held as a draft.
        </p>
      )}
      {o.option_id && (
        <button onClick={() => navigate(`/units/${o.unit_key}?preview=${o.option_id}`)} data-testid={`${id}-show-on-map`}
          className="inline-flex items-center gap-1.5 rounded-full bg-[var(--dp-bg)] px-3 py-1.5 text-xs font-semibold text-[var(--dp-ink)] transition-colors hover:bg-[var(--dp-line)]">
          <MapPin className="h-3.5 w-3.5" /> Show on map
        </button>
      )}
      {actions && o.option_id && <CardActions o={o} id={id} actions={actions} />}
    </div>
  );
}

function BlockedRows({ blocked, prefix }) {
  if (!blocked?.length) return null;
  return (
    <ul className="border border-[var(--dp-line)] bg-[var(--dp-surface)]" data-testid={`${prefix}-blocked`}>
      {blocked.map((b) => (
        <li key={b.unit_key} className="flex items-center gap-2 border-t border-[var(--dp-line)] px-4 py-2.5 text-sm first:border-t-0" data-testid={`${prefix}-blocked-${b.unit_key}`}>
          <Ban className="h-4 w-4 shrink-0 text-[var(--dp-ink-3)]" /> {b.reason}
        </li>
      ))}
    </ul>
  );
}

// Highest-priced option on another van, if it's at least $20 above this card.
function newTripLine(card, options) {
  const far = [...options.cards, ...options.others].filter((o) => o.unit_key !== card.unit_key && o.price >= card.price + 20);
  if (!far.length) return null;
  const top = far.reduce((a, b) => (b.price > a.price ? b : a));
  return `A new trip on ${top.unit_name} would cost $${Number.isInteger(top.price) ? top.price : top.price.toFixed(2)}`;
}

export function OptionCards({ options, prefix, actions }) {
  const [more, setMore] = useState(false);
  if (!options) return null;
  if (!options.cards.length) return (
    <div className="space-y-3">
      <p className="text-sm text-[var(--dp-amber)]" data-testid={`${prefix}-no-options`}>No van can take this, even with a shifted time.</p>
      <BlockedRows blocked={options.blocked} prefix={prefix} />
    </div>
  );
  return (
    <div className="space-y-4" data-testid={`${prefix}-options`}>
      {options.from_shifted && <p className="text-sm text-[var(--dp-amber)]" data-testid={`${prefix}-from-shifted`}>No van can do it as asked. These options use the nearest times that work.</p>}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2 2xl:grid-cols-3">
        {options.cards.map((o, i) => <OptionCard key={o.option_id || i} o={o} id={`${prefix}-option-${i}`} actions={actions} tripLine={newTripLine(o, options)} />)}
      </div>
      <BlockedRows blocked={options.blocked} prefix={prefix} />
      {options.others.length > 0 && (
        <button onClick={() => setMore((m) => !m)} data-testid={`${prefix}-see-other-options`}
          className="inline-flex items-center gap-1.5 rounded-full border border-[var(--dp-line)] px-4 py-2 text-sm font-semibold transition-colors hover:bg-[var(--dp-bg)]">
          <ChevronDown className={`h-4 w-4 transition-transform ${more ? "rotate-180" : ""}`} /> {more ? "Hide other options" : "See other options"}
        </button>
      )}
      {more && (
        <div className="grid grid-cols-1 gap-3 xl:grid-cols-2" data-testid={`${prefix}-other-options`}>
          {options.others.map((o, i) => <OptionCard key={o.option_id || i} o={o} id={`${prefix}-other-${i}`} compact actions={actions} />)}
        </div>
      )}
    </div>
  );
}
