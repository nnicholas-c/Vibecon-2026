import { money, pct, visit } from "../lib/hooks";
import { PrimaryButton, SecondaryButton } from "./Buttons";
import RouteSheet, { Row } from "./RouteSheet";

function Legend() {
  return (
    <div className="lp-rows" data-testid="landing-time-legend">
      <div className="lp-row justify-start gap-3">
        <span className="inline-block h-[4px] w-[26px] bg-[#FF5B1F]" aria-hidden="true" />
        <span>VAN 2</span>
      </div>
      <div className="lp-row justify-start gap-3">
        <span className="inline-block h-[2px] w-[26px] bg-[#141414]" aria-hidden="true" />
        <span>REST OF THE FLEET</span>
      </div>
      <div className="lp-row justify-start gap-3">
        <span className="inline-block h-[12px] w-[24px] rounded-[50%] border-[1.5px] border-[#FF5B1F]" aria-hidden="true" />
        <span>PICKUP WINDOW</span>
      </div>
    </div>
  );
}

function PriceRows({ price }) {
  return (
    <>
      <div className="lp-rows" data-testid="landing-price-rows" data-placeholder={price.placeholder ? "1" : "0"}>
        <Row label={`Extra time, ${price.added_minutes} min`} value={money(price.time_cost)} testid="landing-price-time" />
        <Row label={`Extra miles, ${price.added_miles} mi`} value={money(price.mile_cost)} testid="landing-price-miles" />
        <Row label={`Cost with ${pct(price.markup_pct)} markup`} value={money(price.cost_with_markup)} testid="landing-price-markup" />
        <Row label="Floor price" value={money(price.floor)} testid="landing-price-floor" />
        <Row label="Offer" value={`${visit(price.offer)} a visit`} strong testid="landing-price-offer" />
      </div>
      <p className="lp-rows lp-mono mt-3 text-[11px] text-[#5C5A54]" data-testid="landing-price-note">
        Driver time {money(price.wage_per_hour)} an hour (BLS). Mileage {money(price.cost_per_mile)} a mile (IRS).
      </p>
    </>
  );
}

function Section({ i, children }) {
  return (
    <section className={`lp-sec lp-sec-${i}`} data-testid={`landing-section-${i}`} id={`chapter-${i}`}>
      {children}
    </section>
  );
}

export default function Panels({ price, onPrice, onReplay, plain }) {
  return (
    <>
      <Section i={1}>
        <RouteSheet n="01" name="Fleet" tag="3 vans" title="Three vans, sixteen stops, one afternoon." testid="landing-panel-1">
          <p className="lp-p">Bayline Courier is a demo fleet driving real East Bay streets. Each line is a route a van already runs today.</p>
        </RouteSheet>
      </Section>
      <Section i={2}>
        <RouteSheet n="02" name="Request" tag="Emeryville" side="right" title="A lab in Emeryville wants a daily pickup." testid="landing-panel-2">
          <p className="lp-p">Most couriers would price it as a new trip from the depot. Drivepast first asks which van is already nearby.</p>
          <div className="lp-rows">
            <Row label="Pickup" value="Daily, Mon to Fri" testid="landing-request-pickup" />
            <Row label="Window" value="1:00 to 3:00pm" testid="landing-request-window" />
            <Row label="Usual price" value={`${visit(price.usual)} a visit`} testid="landing-request-usual" />
          </div>
        </RouteSheet>
      </Section>
      <Section i={3}>
        <RouteSheet n="03" name="Time" tag="1 to 3 PM" title="Lift the afternoon and look for a pass." testid="landing-panel-3">
          <p className="lp-p">{"Height is time of day, so each route climbs as its van drives. The ring is the customer's window. Van 2 crosses it at 1:45pm."}</p>
          <Legend />
        </RouteSheet>
      </Section>
      <Section i={4}>
        <RouteSheet n="04" name="Price" tag="Van 2" title="Four extra minutes, 0.6 extra miles." testid="landing-panel-4">
          <p className="lp-p">{"The stop is priced from what it really adds to Van 2's route. Your floor price is the minimum, and the usual price is the cap."}</p>
          <PriceRows price={price} />
        </RouteSheet>
      </Section>
      <Section i={5}>
        <RouteSheet n="05" name="Send" tag="No login" title="Send the offer in one tap." testid="landing-panel-5">
          <p className="lp-p">{"The customer gets an email with an Accept link. When they accept, the stop joins Van 2's route."}</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <PrimaryButton onClick={onPrice} data-testid="landing-send-price-button">
              Price a job
            </PrimaryButton>
            {!plain && (
              <SecondaryButton onClick={onReplay} data-testid="landing-send-replay-button" data-autoplay-control>
                Replay
              </SecondaryButton>
            )}
          </div>
        </RouteSheet>
      </Section>
    </>
  );
}
