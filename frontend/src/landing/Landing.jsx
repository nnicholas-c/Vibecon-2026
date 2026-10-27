import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./fonts";
import Masthead from "./components/Masthead";
import TimelineBar from "./components/TimelineBar";
import Hero from "./components/Hero";
import Panels from "./components/Panels";
import Loader, { ErrorNote } from "./components/Loader";
import { OfferSign, RequestTag } from "./components/PinnedLabels";
import { useLandingPrice, useMotion, useViewportInfo } from "./lib/hooks";
import { usePageColors } from "./lib/pageColors";
import { useSceneBoot } from "./lib/boot";
import { useStory } from "./lib/useStory";

export default function Landing() {
  usePageColors();
  const navigate = useNavigate();
  const vp = useViewportInfo();
  const [motionOn, toggleMotion] = useMotion();
  const reduced = !motionOn;
  const price = useLandingPrice();
  const canvasRef = useRef(null);
  const timelineRef = useRef(null);
  const tagRef = useRef(null);
  const signRef = useRef(null);
  const heroRef = useRef(null);
  const uiRef = useRef({});
  const unitRef = useRef(window.innerHeight);
  const [signOn, setSignOn] = useState(false);
  const getP = useCallback(() => window.scrollY / (unitRef.current || 1), []);

  useEffect(() => {
    const t = timelineRef.current || {};
    uiRef.current.clock = t.clock;
    uiRef.current.marker = t.marker;
    uiRef.current.band = t.band;
    uiRef.current.tag = tagRef.current;
    uiRef.current.sign = signRef.current;
  });

  const boot = useSceneBoot({ canvasRef, uiRef, getP, phone: vp.phone, reduced, onSign: setSignOn });
  const plain = boot.phase === "error" || boot.phase === "fallback";
  const story = useStory({ phase: boot.phase, reduced, unitRef, heroRef, getP, plain, sceneRef: boot.sceneRef });
  const showLoader = !plain && (boot.phase === "loading" || story.loader !== "gone");

  const openInbox = useCallback(() => navigate("/signin"), [navigate]);

  const rootCls = ["lp-root", vp.phone ? "lp-phone" : "", plain ? "lp-plain" : "", reduced ? "lp-reduced" : ""].join(" ");
  return (
    <div className={rootCls} data-testid="landing-page" data-phase={boot.phase}>
      {!plain && (
        <div className="lp-canvas" aria-hidden="true">
          <canvas ref={canvasRef} data-testid="landing-canvas" />
        </div>
      )}
      <main className="lp-main" ref={heroRef}>
        <Hero heroIn={story.heroIn} plain={plain} onPrice={openInbox} onPlay={story.playHere} />
        <Panels price={price} onPrice={openInbox} onReplay={story.replay} plain={plain} />
      </main>
      {!plain && (
        <div className="lp-pins" aria-live="polite">
          <RequestTag ref={tagRef} />
          <OfferSign ref={signRef} on={signOn} phone={vp.phone} price={price} />
        </div>
      )}
      <Masthead
        chapter={story.chapter}
        onChapter={story.goChapter}
        phone={vp.phone}
        motionOn={motionOn}
        onMotion={toggleMotion}
        playMode={story.playMode}
        onPlay={story.onPlayButton}
        onPrice={openInbox}
        plain={plain}
      />
      <TimelineBar ref={timelineRef} phone={vp.phone} initial={plain ? 105 : reduced ? 70 : 30} bandOn={plain} key={plain ? "plain" : "live"} />
      {showLoader && <Loader counts={boot.counts} ready={boot.ready} progress={boot.progress} leaving={story.loader === "leaving"} reduced={reduced} />}
      {boot.phase === "error" && <ErrorNote />}
    </div>
  );
}
