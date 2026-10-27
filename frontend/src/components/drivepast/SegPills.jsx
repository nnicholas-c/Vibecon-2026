import { useLayoutEffect, useRef, useState } from "react";

export function SegPills({ options, value, onChange, testId, size = "md" }) {
  const refs = useRef({});
  const [box, setBox] = useState(null);
  useLayoutEffect(() => {
    const el = refs.current[value];
    if (el) setBox({ left: el.offsetLeft, width: el.offsetWidth });
  }, [value, options]);
  return (
    <div className={`dp-seg ${size === "sm" ? "is-sm" : ""}`} role="tablist" data-testid={testId}>
      {box && <span className="dp-seg-hl" style={{ transform: `translateX(${box.left}px)`, width: box.width }} aria-hidden="true" />}
      {options.map((o) => (
        <button key={o.key} type="button" role="tab" aria-selected={value === o.key} ref={(el) => { refs.current[o.key] = el; }}
          onClick={() => onChange(o.key)} className={`dp-seg-btn ${value === o.key ? "is-on" : ""}`} data-testid={`${testId}-${o.key}`}>
          {o.label}
          {o.count != null && <span className="dp-seg-count tnum" data-testid={`${testId}-${o.key}-count`}>{o.count}</span>}
        </button>
      ))}
    </div>
  );
}

export const PERIODS = [{ key: "today", label: "Today" }, { key: "week", label: "This week" }];
export const WEEK_DAYS = 5;
