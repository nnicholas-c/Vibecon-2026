import { useNavigate } from "react-router-dom";
import { MapPin } from "lucide-react";
import { money } from "@/lib/format";
import { OptionCards } from "../OptionCards";

function VanRow({ r, winnerKey }) {
  const win = r.unit_key === winnerKey;
  return (
    <tr className={`border-b border-[var(--dp-line)] last:border-0 ${win ? "bg-[var(--dp-green-soft)]" : ""}`} data-testid={`engine-row-${r.unit_key}`}>
      <td className="whitespace-nowrap px-3 py-2.5">
        <span className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ background: r.color }} />
          <span className="font-medium">{r.unit_name}</span>
          {win && <span className="rounded-full bg-[var(--dp-green)] px-2 py-0.5 text-[11px] font-medium text-[#111214]" data-testid={`engine-winner-badge-${r.unit_key}`}>Winner</span>}
        </span>
      </td>
      {r.feasible ? (
        <>
          <td className="tnum px-3 py-2.5 text-right" data-testid={`engine-min-${r.unit_key}`}>+{r.added_minutes} min</td>
          <td className="tnum px-3 py-2.5 text-right" data-testid={`engine-mi-${r.unit_key}`}>+{r.added_miles.toFixed(1)} mi</td>
          <td className="tnum px-3 py-2.5 text-right" data-testid={`engine-cost-${r.unit_key}`}>{money(r.added_cost)}</td>
          <td className="px-3 py-2.5 text-xs text-[var(--dp-ink-2)]">{r.new_stops.map((n) => `${n.name} ${n.arrival_label}`).join(", ")}</td>
        </>
      ) : (
        <td colSpan={4} className="px-3 py-2.5 text-sm" data-testid={`engine-reason-${r.unit_key}`}>
          <span className={r.reason === "missing skill" ? "text-[var(--dp-red)]" : "text-[var(--dp-amber)]"}>Can't: {r.reason}</span>
          <span className="text-xs text-[var(--dp-ink-3)]"> | around then: {r.where.area}, until {r.where.until_label}</span>
        </td>
      )}
    </tr>
  );
}

function WinnerBlock({ w, n, label }) {
  const navigate = useNavigate();
  return (
    <div className="space-y-1.5 rounded-lg border border-[var(--dp-line)] bg-[var(--dp-surface)] p-4" data-testid={`engine-winner-${n}`}>
      <p className="text-xs uppercase tracking-wider text-[var(--dp-ink-3)]">{label}</p>
      <p className="font-display text-xl font-semibold text-[var(--dp-green)]">
        {w.unit_name}: <span className="tnum" data-testid={`engine-price-${n}`}>{money(w.price)}</span> a {w.per}
        {w.monthly_total != null && <span className="tnum text-base text-[var(--dp-ink-2)]"> ({money(w.monthly_total)} a month)</span>}
      </p>
      <p className="text-sm" data-testid={`engine-explanation-${n}`}>{w.explanation}</p>
      {w.pass_by && <p className="text-sm text-[var(--dp-ink-2)]" data-testid={`engine-passby-${n}`}>{w.pass_by.line}</p>}
      {w.market_line && <p className="text-sm text-[var(--dp-ink-2)]" data-testid={`engine-market-${n}`}>{w.market_line}</p>}
      <p className="tnum text-xs text-[var(--dp-ink-3)]" data-testid={`engine-handcheck-${n}`}>Hand check: {w.hand_check}</p>
      {w.option_id && (
        <button onClick={() => navigate(`/units/${w.unit_key}?preview=${w.option_id}`)} data-testid={`engine-show-on-map-${n}`}
          className="mt-1 inline-flex items-center gap-1.5 rounded-lg bg-[var(--dp-ink)] px-3 py-2 text-xs font-semibold tracking-wide text-[var(--dp-page)] transition-opacity hover:opacity-85">
          <MapPin className="h-3.5 w-3.5" /> Show on map
        </button>
      )}
    </div>
  );
}

export function RequestResult({ res }) {
  const n = res.number;
  if (res.error) return <p className="text-sm text-[var(--dp-amber)]" data-testid={`engine-error-${n}`}>{res.error}</p>;
  const sh = res.shifted;
  return (
    <div className="space-y-3" data-testid={`engine-result-${n}`}>
      {res.winner && <WinnerBlock w={res.winner} n={n} label="Best van" />}
      {sh && (
        <div className="rounded-lg bg-[var(--dp-amber-soft)] p-4 text-sm" data-testid={`engine-shifted-${n}`}>
          <p className="font-medium text-[var(--dp-amber)]">No van can do it as asked.</p>
          <p className="mt-1" data-testid={`engine-shifted-line-${n}`}>{sh.line}</p>
        </div>
      )}
      {sh?.winner && <WinnerBlock w={sh.winner} n={`${n}-shifted`} label="Working option" />}
      {res.options && <OptionCards options={res.options} prefix={`engine-${n}`} />}
      <div className="overflow-x-auto rounded-lg border border-[var(--dp-line)] bg-[var(--dp-surface)]">
        <table className="w-full min-w-[560px] text-sm">
          <tbody>{res.results.map((r) => <VanRow key={r.unit_key} r={r} winnerKey={res.winner_unit_key} />)}</tbody>
        </table>
      </div>
      <p className="tnum text-xs text-[var(--dp-ink-3)]" data-testid={`engine-ms-${n}`}>Engine time {res.ms} ms</p>
    </div>
  );
}
