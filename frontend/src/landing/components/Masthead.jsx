import { useState } from "react";
import { Pause, Play, RotateCcw } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { CHAPTERS } from "../lib/constants";
import { Wordmark } from "./Mark";
import { PrimaryButton, SecondaryButton } from "./Buttons";

function ChapterButtons({ chapter, onChapter }) {
  return (
    <nav className="hidden h-full min-[900px]:flex" aria-label="Chapters" data-testid="landing-chapter-nav">
      {CHAPTERS.map((c, i) => {
        const cur = chapter === i + 1;
        return (
          <button
            key={c.n}
            type="button"
            onClick={() => onChapter(c.p)}
            aria-current={cur ? "step" : undefined}
            className={`lp-chap ${cur ? "lp-chap-on" : ""}`}
            data-testid={`landing-chapter-${c.n}`}
          >
            <span className="font-semibold">{c.n}</span>
            <span className={cur ? "inline" : "hidden min-[1180px]:inline"}>{c.name}</span>
          </button>
        );
      })}
    </nav>
  );
}

function PlayButton({ mode, phone, onClick }) {
  const Icon = mode === "Pause" ? Pause : mode === "Replay" ? RotateCcw : Play;
  return (
    <SecondaryButton
      onClick={onClick}
      aria-label={phone ? mode : undefined}
      className={`lp-mono-btn ${phone ? "w-11 justify-center px-0" : ""}`}
      data-testid="landing-play-button"
      data-autoplay-control
    >
      <Icon size={14} strokeWidth={2.2} aria-hidden="true" />
      {!phone && <span>{mode}</span>}
    </SecondaryButton>
  );
}

export default function Masthead({ chapter, onChapter, phone, motionOn, onMotion, playMode, onPlay, onPrice, plain }) {
  const navigate = useNavigate();
  const [opening, setOpening] = useState(false);
  const openIt = () => { setOpening(true); navigate("/signin"); };
  return (
    <header className="lp-masthead" data-testid="landing-masthead">
      <Link to="/" className="lp-focus flex h-full items-center" aria-label="Drivepast home" data-testid="landing-home-link">
        <Wordmark />
      </Link>
      {!phone && <ChapterButtons chapter={chapter} onChapter={onChapter} />}
      <div className="flex items-center gap-2">
        {!phone && (
          <span className="lp-label hidden text-[#5C5A54] min-[1240px]:inline" data-testid="landing-masthead-label">
            Demo fleet, Bayline Courier
          </span>
        )}
        {!phone && !plain && (
          <SecondaryButton onClick={onMotion} aria-pressed={motionOn} className="lp-mono-btn" data-testid="landing-motion-toggle" data-autoplay-control>
            {motionOn ? "Motion on" : "Motion off"}
          </SecondaryButton>
        )}
        {!plain && <PlayButton mode={playMode} phone={phone} onClick={onPlay} />}
        <PrimaryButton onClick={onPrice} className="whitespace-nowrap" data-testid="landing-masthead-price-button">
          Price a job
        </PrimaryButton>
        <SecondaryButton onClick={openIt} disabled={opening} className="whitespace-nowrap" data-testid="landing-masthead-demo-button">
          {opening ? "Opening…" : "Open the demo"}
        </SecondaryButton>
      </div>
    </header>
  );
}
