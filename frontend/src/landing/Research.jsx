import { Link, useNavigate } from "react-router-dom";
import "./fonts";
import { Wordmark } from "./components/Mark";
import { usePageColors } from "./lib/pageColors";

const FINDINGS = [
  {
    fact: "There are 5,367 local courier businesses in the US.",
    source: "US Census, County Business Patterns 2023, NAICS 492210",
    answer: "Drivepast is for these small fleets, the ones with a few vans and an inbox but nobody whose job is dispatch.",
  },
  {
    fact: "An extra stop on a route a van already drives costs about $3.50 to $4. An average stop costs about $12.28.",
    source: "Routerra route-cost benchmark",
    answer: "The pricing engine finds the van that already passes nearby and prices from that small added cost.",
  },
  {
    fact: "In the Bay Area, an on-demand courier run costs $45 to $65.",
    source: "Published rates of local Bay Area couriers",
    answer: "Each quote shows the drive-past price next to your usual price, so the customer sees the saving.",
  },
  {
    fact: "Leads answered within an hour are nearly 7 times as likely to qualify as leads answered later.",
    source: "Harvard Business Review, 2011",
    answer: "New emails are read and priced as soon as they arrive, and the quote can go out on its own within your rules.",
  },
];

const INTERVIEWS = [1, 2, 3];

function Finding({ f, i }) {
  return (
    <li className="lp-row flex-col items-start justify-start gap-1 text-left" data-testid={`research-finding-${i + 1}`}>
      <span className="w-full text-left font-semibold">{f.fact}</span>
      <span className="w-full text-left text-[13px] text-[#5C5A54]" data-testid={`research-source-${i + 1}`}>Source: {f.source}</span>
      <span className="w-full text-left text-[13px]" data-testid={`research-answer-${i + 1}`}>What Drivepast does: {f.answer}</span>
    </li>
  );
}

export default function Research() {
  usePageColors();
  const navigate = useNavigate();
  return (
    <div className="lp-root min-h-screen" data-testid="research-page">
      <header className="lp-masthead">
        <Link to="/" className="lp-focus flex h-full items-center" aria-label="Drivepast home" data-testid="research-home-link">
          <Wordmark testid="research-wordmark" />
        </Link>
        <button type="button" onClick={() => navigate("/signin")} className="lp-btn lp-btn-primary lp-focus" data-testid="research-demo-link">
          Open the demo
        </button>
      </header>
      <main className="px-[clamp(12px,3.4vw,52px)] pb-24 pt-[120px]">
        <div className="lp-sheet static" style={{ width: "min(760px, 100%)" }}>
          <div className="lp-sheet-head">
            <span className="lp-sheet-num">r</span>
            <span className="flex-1 px-3">Our research</span>
            <span className="pr-3 text-[#5C5A54]">Sources</span>
          </div>
          <div className="lp-sheet-body">
            <h1 className="lp-h2" data-testid="research-title">Our research</h1>
            <p className="lp-p">What we found about small courier fleets, and what Drivepast does about each finding.</p>
            <ul className="lp-rows" data-testid="research-findings">
              {FINDINGS.map((f, i) => <Finding key={f.fact} f={f} i={i} />)}
            </ul>
            <h2 className="lp-h2 mt-8 text-[22px]" data-testid="research-interviews-title">Owner interviews</h2>
            <ul className="lp-rows" data-testid="research-interviews">
              {INTERVIEWS.map((n) => (
                <li key={n} className="lp-row flex-col items-start justify-start gap-1 text-left text-[#5C5A54]" data-testid={`research-interview-${n}`}>
                  <span className="w-full text-left font-semibold">[Placeholder] Interview {n}: owner name, company, fleet size</span>
                  <span className="w-full text-left text-[13px]">[Placeholder] What they said, in their words.</span>
                </li>
              ))}
            </ul>
            <div className="mt-6">
              <Link to="/" className="lp-btn lp-btn-secondary lp-focus" data-testid="research-back-link">Back to the story</Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
