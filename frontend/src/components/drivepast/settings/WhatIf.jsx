import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useFleet } from "@/context/FleetContext";
import { friendlyMessage, http } from "@/lib/api";

const selectCls = "h-11 w-full rounded-lg border border-[var(--dp-line)] bg-[var(--dp-surface)] px-3 text-sm outline-none focus:border-[var(--dp-green)]";

export function WhatIf() {
  const { fleet } = useFleet();
  const [stops, setStops] = useState([]);
  const [stopKey, setStopKey] = useState("");
  const [target, setTarget] = useState("");
  const [out, setOut] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    http.get("/stops").then(({ data }) => setStops(data.filter((s) => s.recurrence === "weekday"))).catch(() => setError("Couldn't load the stops. Try again."));
  }, []);

  const units = fleet?.units || [];
  const from = stops.find((s) => s.key === stopKey)?.unit_key;
  const run = async () => {
    setBusy(true);
    setError("");
    setOut(null);
    try {
      const { data } = await http.post("/engine/what-if", { stop_key: stopKey, to_unit_key: target });
      setOut(data);
    } catch (err) {
      setError(friendlyMessage(err, "The engine hit a problem on this request. Try again."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="dp-card p-5 sm:p-6" data-testid="engine-what-if">
      <h2 className="text-base font-semibold md:text-lg">What if we move a stop?</h2>
      <p className="mt-1 text-sm text-[var(--dp-ink-2)]">See what changes for both vans. Nothing is saved.</p>
      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-[1fr_180px_auto]">
        <select value={stopKey} onChange={(e) => setStopKey(e.target.value)} className={selectCls} data-testid="what-if-stop-select">
          <option value="">Pick a stop</option>
          {units.map((u) => (
            <optgroup key={u.key} label={u.name}>
              {stops.filter((s) => s.unit_key === u.key).map((s) => <option key={s.key} value={s.key}>{s.customer_name}, {s.address}</option>)}
            </optgroup>
          ))}
        </select>
        <select value={target} onChange={(e) => setTarget(e.target.value)} className={selectCls} data-testid="what-if-target-select">
          <option value="">Move to</option>
          {units.filter((u) => u.key !== from).map((u) => <option key={u.key} value={u.key}>{u.name}</option>)}
        </select>
        <Button className="h-11 rounded-lg font-semibold tracking-wide" disabled={!stopKey || !target || busy} onClick={run} data-testid="what-if-run-button">
          {busy ? "Checking..." : "Try it"}
        </Button>
      </div>
      {error && <p className="mt-3 text-sm text-[var(--dp-amber)]" data-testid="what-if-error">{error}</p>}
      {out && (
        <div className="mt-4 space-y-1 text-sm" data-testid="what-if-result">
          <p data-testid="what-if-from-line">{out.from.line}</p>
          <p className={out.to.feasible ? "" : "text-[var(--dp-amber)]"} data-testid="what-if-to-line">{out.to.line}</p>
        </div>
      )}
    </div>
  );
}
