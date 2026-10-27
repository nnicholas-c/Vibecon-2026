import { forwardRef } from "react";
import { visit } from "../lib/hooks";

export const RequestTag = forwardRef(function RequestTag(_, ref) {
  return (
    <div ref={ref} className="lp-pin-anchor lp-request-tag-wrap" style={{ opacity: 0 }} aria-hidden="true" data-testid="landing-request-tag">
      <div className="lp-tag">
        <div className="lp-tag-head">NEW REQUEST</div>
        <div className="lp-tag-row">
          <span className="text-[#5C5A54]">Pickup</span>
          <span>Daily, Mon to Fri</span>
        </div>
        <div className="lp-tag-row">
          <span className="text-[#5C5A54]">Window</span>
          <span>1:00 to 3:00pm</span>
        </div>
      </div>
    </div>
  );
});

export const OfferSign = forwardRef(function OfferSign({ on, phone, price }, ref) {
  return (
    <div ref={ref} className={`lp-pin-anchor ${phone ? "lp-sign-dock" : ""}`} data-testid="landing-offer-sign-anchor">
      <div className={`lp-sign-lift ${phone ? "" : "lp-sign-up"}`}>
        <div className={`lp-sign ${on ? "lp-sign-on" : ""}`} role="status" aria-hidden={!on} data-testid="landing-offer-sign">
          <div className="lp-sign-inner">
            <div className="flex items-center gap-2 lp-mono text-[12px] font-semibold uppercase tracking-[0.08em]">
              <span className="lp-sign-badge">2</span>
              <span className="flex-1">VAN 2 PASSES</span>
              <span>DAILY</span>
            </div>
            <p className="lp-sign-time">1:45 PM</p>
            <p className="lp-sign-line">Our van already passes your door at 1:45pm.</p>
            <div className="lp-sign-rule">
              <span className="text-[15px]">Add a daily pickup</span>
              <span data-testid="landing-sign-price">
                <span className="text-[24px] font-extrabold">{visit(price.offer)}</span>
                <span className="text-[13px]"> a visit</span>
              </span>
            </div>
            <p className="lp-mono mt-1 text-[12px] text-[#D7E6E0]" data-testid="landing-sign-usual">
              USUALLY {visit(price.usual)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
});
