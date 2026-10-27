import { useEffect, useRef, useState } from "react";

// "+$N" for ~1.5 s when the saved-today tally goes up (a booking); nothing on Undo or Reset.
export function SavedBump({ value }) {
  const prev = useRef(value);
  const [bump, setBump] = useState(null);
  useEffect(() => {
    const before = prev.current;
    prev.current = value;
    if (before == null || value == null || value <= before + 0.004) return undefined;
    setBump({ n: value - before, id: Date.now() });
    const t = setTimeout(() => setBump(null), 1500);
    return () => clearTimeout(t);
  }, [value]);
  if (!bump) return null;
  const n = Number.isInteger(bump.n) ? bump.n : bump.n.toFixed(2);
  return <span key={bump.id} className="dp-saved-bump" data-testid="dispatch-saved-bump">+${n}</span>;
}
