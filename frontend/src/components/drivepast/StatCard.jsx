import { useEffect, useState } from "react";
import { createPortal } from "react-dom";


export function StatChips({ items, testPrefix }) {
  const [slot, setSlot] = useState(null);
  useEffect(() => setSlot(document.getElementById("dp-topbar-chips")), []);
  const body = (
    <div className="dp-chips flex flex-wrap" data-testid={`${testPrefix}s`}>
      {items.map(([key, label, value, raw], i) => (
        <span key={key} className="dp-chip" style={{ animationDelay: `${i * 40}ms` }} data-testid={`${testPrefix}-${key}`}>
          {label}{raw ? " " : ": "}<b>{value}</b>
        </span>
      ))}
    </div>
  );
  return slot ? createPortal(body, slot) : null;
}

export function StatCard({ label, value, hint, testId, tone = "ink" }) {
  const color = tone === "green" ? "text-[var(--dp-green)]" : "text-[var(--dp-ink)]";
  return (
    <div className="dp-card p-5" data-testid={testId}>
      <p className="text-xs font-medium uppercase tracking-wider text-[var(--dp-ink-3)]">{label}</p>
      <p className={`tnum mt-2 font-display text-2xl font-semibold ${color}`} data-testid={`${testId}-value`}>{value}</p>
      {hint && <p className="mt-1 text-xs text-[var(--dp-ink-2)]">{hint}</p>}
    </div>
  );
}
