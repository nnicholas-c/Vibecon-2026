// Boot: load and decode the kit, start deck.gl, report loader progress, fall back on failure (PROMPT.md 3.5, 3.6, 6).
import { useEffect, useRef, useState } from "react";
import { checkSample, decodeBuildings, decodeFleet, decodeMeta, decodeRoads, decodeShadows, decodeSurroundings, decodeWater } from "./decode";
import { FIRST_VIEW, SIZES, fetchJSON, hasWebGL2, waitFonts } from "./data";

const TOTAL = FIRST_VIEW.reduce((s, n) => s + SIZES[n], 0);

export function useSceneBoot({ canvasRef, uiRef, getP, phone, reduced, onSign }) {
  const [phase, setPhase] = useState("loading"); // loading | ready | error | fallback
  const [ready, setReady] = useState({ roads: false, buildings: false, fleet: false });
  const [progress, setProgress] = useState(0);
  const [counts, setCounts] = useState(null);
  const sceneRef = useRef(null);
  const opts = useRef({ phone, reduced, onSign });
  opts.current = { phone, reduced, onSign };

  useEffect(() => {
    let dead = false;
    let errTimer = 0;
    const fail = (why) => {
      if (dead) return;
      dead = true;
      console.warn("[landing] 3D view fallback:", why);
      sceneRef.current?.destroy();
      sceneRef.current = null;
      setPhase("error");
      errTimer = setTimeout(() => setPhase("fallback"), 4000);
    };
    if (!hasWebGL2()) {
      fail("WebGL2 not available");
      return () => clearTimeout(errTimer);
    }
    const noTimeout = () => window.__lpNoTimeout || new URLSearchParams(window.location.search).get("e2e") === "1";
    const timeout = setTimeout(() => !noTimeout() && fail("first view not ready after 12s"), 12000);
    let got = 0;
    const onBytes = (n) => {
      got += n;
      setProgress(Math.min(1, got / TOTAL));
    };
    const mark = (k) => !dead && setReady((r) => ({ ...r, [k]: true }));
    const boot = async () => {
      const deckP = import(
        /* webpackChunkName: "deckgl", webpackExports: ["Deck", "MapView", "WebMercatorViewport", "LightingEffect", "AmbientLight", "DirectionalLight", "SolidPolygonLayer", "PathLayer", "ScatterplotLayer", "TextLayer", "LineLayer", "TripsLayer", "SimpleMeshLayer"] */ "deck.gl"
      );
      const fontsP = waitFonts();
      const [metaP, fleetP, waterP, surrP, roadsP, bP, sP] = FIRST_VIEW.map((n) => fetchJSON(n, onBytes));
      const T0 = performance.now();
      const lg = (k) => console.info(`[landing] ${k} ${Math.round(performance.now() - T0)}ms`);
      const meta = decodeMeta(await metaP);
      setCounts(meta.counts);
      fetchJSON("sample").then((s) => {
        const fails = checkSample(s, meta.raw);
        if (fails.length) console.error("[landing] decoder check failed", fails);
        else console.info("[landing] decoder check passed against sample.json");
      });
      const c = meta.coder;
      const fleet = decodeFleet(await fleetP, c).filter((v) => v.id <= 3);
      setCounts({ ...meta.counts, vans: fleet.length, stops: fleet.reduce((n, v) => n + v.stops.length, 0) });
      mark("fleet");
      const water = decodeWater(await waterP, c);
      const surroundings = decodeSurroundings(await surrP, c);
      const roads = decodeRoads(await roadsP, c);
      mark("roads");
      const buildings = decodeBuildings(await bP, c);
      mark("buildings");
      const shadows = decodeShadows(await sP, c);
      lg("data decoded");
      const D = await deckP;
      await fontsP;
      lg("deck+fonts");
      if (dead) return;
      const { Scene } = await import("./scene");
      sceneRef.current = new Scene({
        D,
        canvas: canvasRef.current,
        data: { meta, fleet, water, surroundings, roads, buildings, shadows },
        phone: opts.current.phone,
        reduced: opts.current.reduced,
        ui: uiRef.current,
        getP,
        onSign: (on) => opts.current.onSign(on),
        onError: (e) => fail(e?.message || "deck.gl error"),
        onReady: () => {
          clearTimeout(timeout);
          lg("first view ready");
          if (!dead) setPhase("ready");
        },
      });
      if (!opts.current.phone) {
        Promise.all([fetchJSON("buildings-rest"), fetchJSON("shadows-rest")])
          .then(([b, s]) => !dead && sceneRef.current?.addRest(b, s))
          .catch((e) => console.warn("[landing] rest layers skipped", e));
      }
    };
    boot().catch((e) => fail(e?.message || "load failed"));
    return () => {
      dead = true;
      clearTimeout(timeout);
      clearTimeout(errTimer);
      sceneRef.current?.destroy();
      sceneRef.current = null;
    };
  }, [canvasRef, uiRef, getP]);

  useEffect(() => {
    if (sceneRef.current) sceneRef.current.phone = phone;
  }, [phone]);
  useEffect(() => {
    sceneRef.current?.setReduced(reduced);
  }, [reduced]);

  return { phase, ready, progress, counts, sceneRef };
}
