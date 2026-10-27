import { forwardRef, useImperativeHandle, useRef } from "react";
import { Link } from "react-router-dom";
import { CREDIT_LONG, CREDIT_SHORT } from "../lib/constants";
import { fmtClock, rulerPct } from "../lib/story";

const TICKS = Array.from({ length: 15 }, (_, i) => i * 15);
const HOURS = ["12 PM", "1 PM", "2 PM", "3 PM"];

function Ruler({ phone, bandRef, markerRef, initial, bandOn }) {
  return (
    <div className="relative h-[44px] w-full" data-testid="landing-ruler">
      <div className="absolute inset-x-0 top-[22px] h-px bg-[#141414]" />
      <div
        ref={bandRef}
        className="absolute top-[8px] h-[14px] border border-[#FF5B1F] bg-[#FF5B1F]/[0.18]"
        style={{ left: `${rulerPct(60)}%`, width: `${rulerPct(120)}%`, opacity: bandOn ? 1 : 0 }}
        data-testid="landing-window-band"
      />
      {TICKS.map((m) => (
        <span
          key={m}
          className={`absolute top-[22px] w-px bg-[#141414] ${m % 60 === 0 ? "h-[15px]" : "h-[8px]"}`}
          style={{ left: `${rulerPct(m)}%` }}
        />
      ))}
      {!phone &&
        HOURS.map((h, i) => (
          <span key={h} className="lp-mono absolute top-[38px] -translate-x-1/2 text-[10px] leading-none text-[#5C5A54]" style={{ left: `${rulerPct(i * 60)}%` }}>
            {h}
          </span>
        ))}
      <span
        ref={markerRef}
        className="lp-marker absolute top-[6px] h-[32px] w-[5px] -translate-x-1/2 border border-[#141414] bg-[#FF5B1F]"
        style={{ left: `${rulerPct(initial)}%` }}
        data-testid="landing-time-marker"
      />
    </div>
  );
}

const TimelineBar = forwardRef(function TimelineBar({ phone, initial = 30, bandOn = false }, ref) {
  const clockRef = useRef(null);
  const markerRef = useRef(null);
  const bandRef = useRef(null);
  useImperativeHandle(ref, () => ({ clock: clockRef.current, marker: markerRef.current, band: bandRef.current }), []);
  return (
    <footer className="lp-timeline" data-testid="landing-timeline">
      <div className="shrink-0">
        <p className="lp-label text-[11px] text-[#5C5A54]">Bayline time</p>
        <p ref={clockRef} className="lp-clock" data-testid="landing-clock">
          {fmtClock(initial)}
        </p>
      </div>
      <div className="flex min-w-0 flex-1 flex-col">
        <Ruler phone={phone} bandRef={bandRef} markerRef={markerRef} initial={initial} bandOn={bandOn} />
        {phone && (
          <span className="absolute bottom-[5px] right-[var(--lp-pad)] flex gap-3 whitespace-nowrap text-[10px] leading-none">
            <Link to="/research" className="lp-focus font-semibold text-[#141414] underline" data-testid="landing-research-link-short">Our research</Link>
            <Link to="/about" className="lp-focus text-[#5C5A54]" data-testid="landing-credit-short">{CREDIT_SHORT}</Link>
          </span>
        )}
      </div>
      {!phone && (
        <div className="flex max-w-[330px] shrink flex-col gap-1">
          <Link to="/about" className="lp-focus text-[11px] leading-[1.35] text-[#5C5A54] hover:text-[#141414]" data-testid="landing-credit-line">
            {CREDIT_LONG}
          </Link>
          <Link to="/research" className="lp-focus text-[11px] font-semibold leading-none text-[#141414] underline" data-testid="landing-research-link">
            Our research
          </Link>
        </div>
      )}
    </footer>
  );
});

export default TimelineBar;
