// Scroll, chapters, the loader hand-off and autoplay (PROMPT.md 3.5, 5.7).
import { useCallback, useEffect, useRef, useState } from "react";
import { Player, fullScript, scriptFrom } from "./autoplay";
import { chapterAt } from "./story";

const SCROLL_KEYS = new Set(["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End", " ", "Spacebar"]);
const isControl = (e) => Boolean(e.target?.closest?.("[data-autoplay-control]"));

function plainChapter() {
  let c = 0;
  for (let i = 1; i <= 5; i++) {
    const el = document.getElementById(`chapter-${i}`);
    if (el && el.getBoundingClientRect().top < window.innerHeight * 0.45) c = i;
  }
  return c;
}

export function useStory({ phase, reduced, unitRef, heroRef, getP, plain, sceneRef }) {
  const [chapter, setChapter] = useState(0);
  const [atEnd, setAtEnd] = useState(false);
  const [mode, setMode] = useState("idle");
  const [heroIn, setHeroIn] = useState(false);
  const [loader, setLoader] = useState("cover");
  const touched = useRef(false);
  const reducedRef = useRef(reduced);
  reducedRef.current = reduced;
  const playerRef = useRef(null);
  if (!playerRef.current) playerRef.current = new Player({ getUnit: () => unitRef.current, getP, onState: setMode });
  const player = playerRef.current;

  useEffect(() => {
    const measure = () => {
      const s = heroRef.current?.firstElementChild;
      unitRef.current = s?.offsetHeight || window.innerHeight;
    };
    const onScroll = () => {
      const P = getP();
      setChapter(plain ? plainChapter() : chapterAt(P));
      setAtEnd(!plain && P > 5.45);
    };
    measure();
    onScroll();
    const onResize = () => {
      measure();
      onScroll();
    };
    window.addEventListener("resize", onResize);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("resize", onResize);
      window.removeEventListener("scroll", onScroll);
    };
  }, [plain, getP, heroRef, unitRef]);

  // Any wheel, touch, pointer press or scrolling key takes over.
  useEffect(() => {
    const stop = () => {
      touched.current = true;
      player.stop();
    };
    const onPointer = (e) => !isControl(e) && stop();
    const onKey = (e) => {
      touched.current = true;
      if (SCROLL_KEYS.has(e.key) && !isControl(e)) player.stop();
    };
    window.addEventListener("wheel", stop, { passive: true });
    window.addEventListener("touchstart", onPointer, { passive: true });
    window.addEventListener("pointerdown", onPointer);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("wheel", stop);
      window.removeEventListener("touchstart", onPointer);
      window.removeEventListener("pointerdown", onPointer);
      window.removeEventListener("keydown", onKey);
      player.stop();
    };
  }, [player]);

  // Loader leaves ~600ms after the first view is ready; hero text 950ms later; autoplay at 2.6s.
  useEffect(() => {
    if (phase !== "ready") return undefined;
    const timers = [];
    timers.push(
      setTimeout(() => {
        setLoader("leaving");
        sceneRef.current?.beginIntro();
        timers.push(setTimeout(() => setHeroIn(true), reducedRef.current ? 0 : 950));
        timers.push(setTimeout(() => setLoader("gone"), 1100));
        timers.push(
          setTimeout(() => {
            if (!touched.current && !reducedRef.current && window.scrollY < 2) player.run(fullScript(), 0);
          }, 2600),
        );
      }, 600),
    );
    return () => timers.forEach(clearTimeout);
  }, [phase, player, sceneRef]);

  useEffect(() => {
    if (reduced) player.stop();
  }, [reduced, player]);

  const replay = useCallback(() => {
    touched.current = true;
    window.scrollTo(0, 0);
    player.run(fullScript(), 0);
  }, [player]);

  const playHere = useCallback(() => {
    touched.current = true;
    const s = scriptFrom(getP());
    if (!s) return replay();
    player.run(s, 0.8);
    return undefined;
  }, [player, getP, replay]);

  const onPlayButton = useCallback(() => {
    if (mode === "playing") player.stop();
    else if (atEnd) replay();
    else playHere();
  }, [mode, atEnd, player, replay, playHere]);

  const goChapter = useCallback(
    (p) => {
      touched.current = true;
      if (plain) {
        document.getElementById(`chapter-${Math.min(5, Math.floor(p))}`)?.scrollIntoView({ block: "start" });
      } else if (reducedRef.current) {
        player.stop();
        window.scrollTo(0, p * unitRef.current);
      } else player.glide(p);
    },
    [plain, player, unitRef],
  );

  const playMode = mode === "playing" ? "Pause" : atEnd ? "Replay" : "Play";
  return { chapter, playMode, onPlayButton, playHere, replay, goChapter, heroIn: heroIn || plain, loader };
}
