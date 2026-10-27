import { ArrowRight, Play } from "lucide-react";
import { PrimaryButton, SecondaryButton } from "./Buttons";

const LINES = ["Price every job", "from the van that", "already drives past."];

export default function Hero({ heroIn, plain, onPrice, onPlay }) {
  const cls = plain ? "lp-hero-static" : heroIn ? "lp-hero-in" : "lp-hero-wait";
  return (
    <section className={`lp-sec lp-sec-hero ${cls}`} data-testid="landing-hero">
      <div className="max-w-[640px]">
        <p className="lp-kicker flex items-center gap-3" data-testid="landing-hero-kicker">
          <span className="inline-block h-[2px] w-[28px] bg-[#141414]" aria-hidden="true" />
          <span className="lp-label">For courier companies with 2 to 20 vans</span>
        </p>
        <h1 className="lp-h1" data-testid="landing-hero-title">
          {LINES.map((l, i) => (
            <span key={l} className="lp-mask">
              <span className="lp-line" style={{ "--d": `${150 + i * 90}ms` }}>
                {l}
              </span>
            </span>
          ))}
        </h1>
        <p className="lp-hero-body" data-testid="landing-hero-body">
          Drivepast checks each new stop against the routes your vans already run, then prices it from the real extra minutes and miles.
        </p>
        <div className="lp-hero-buttons flex flex-wrap gap-3">
          <PrimaryButton onClick={onPrice} data-testid="landing-hero-price-button">
            Price a job <ArrowRight size={16} strokeWidth={2.4} aria-hidden="true" />
          </PrimaryButton>
          {!plain && (
            <SecondaryButton onClick={onPlay} data-testid="landing-hero-play-button" data-autoplay-control>
              <Play size={14} strokeWidth={2.4} aria-hidden="true" /> Play the afternoon
            </SecondaryButton>
          )}
        </div>
      </div>
      {!plain && (
        <div className="lp-cue" aria-hidden="true" data-testid="landing-scroll-cue">
          <span className="lp-cue-track">
            <span className="lp-cue-dot" />
          </span>
          <span className="lp-label text-[11px]">Scroll to follow Van 2</span>
        </div>
      )}
    </section>
  );
}
