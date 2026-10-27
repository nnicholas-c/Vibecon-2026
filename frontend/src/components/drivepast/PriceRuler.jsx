import { useEffect, useState } from "react";
import "@fontsource/overpass-mono/600.css";

const reduced = () => Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)").matches);
const usd = (n) => `$${Number.isInteger(n) ? n : n.toFixed(2)}`;

// $0 to the usual price; the accent marker slides from the usual price down to the quoted one.
export function PriceRuler({ price, usual }) {
  const target = Math.max(0, Math.min(100, (price / usual) * 100));
  const [x, setX] = useState(reduced() ? target : 100);
  useEffect(() => {
    if (reduced()) return undefined;
    const t = setTimeout(() => setX(target), 350);
    return () => clearTimeout(t);
  }, [target]);
  return (
    <div className="flex flex-wrap items-end gap-x-3 gap-y-2">
    <div className="dp-ruler min-w-[180px] flex-1" data-testid="booking-price-ruler" data-price={price} data-usual={usual}>
      <div className="dp-ruler-track">
        <span className="dp-ruler-tick" style={{ left: "0%" }} />
        <span className="dp-ruler-tick" style={{ left: "100%" }} />
        <span className="dp-ruler-usual" style={{ left: "100%" }} data-testid="booking-ruler-usual">{usd(usual)}</span>
        <span className="dp-ruler-marker" style={{ left: `${x}%` }} data-testid="booking-ruler-marker" />
        <span className="dp-ruler-price" style={{ left: `${x}%` }} data-testid="booking-ruler-price">{usd(price)}</span>
      </div>
      <div className="dp-ruler-zero">$0</div>
    </div>
    {usual > price && (
      <span className="shrink-0 whitespace-nowrap border border-[var(--dp-ink)] bg-[var(--dp-page)] px-2 py-1 text-[11px] font-semibold leading-none text-[var(--dp-ink)]"
        style={{ fontFamily: '"Overpass Mono", ui-monospace, monospace' }} data-testid="booking-customer-saving">
        Saves the customer {usd(Math.round((usual - price) * 100) / 100)}
      </span>
    )}
    </div>
  );
}
