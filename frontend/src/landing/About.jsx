import { Link, useNavigate } from "react-router-dom";
import "./fonts";
import { Wordmark } from "./components/Mark";
import { usePageColors } from "./lib/pageColors";

// Section 8 lines, exactly.
const CREDITS = [
  "Map data © OpenStreetMap contributors",
  "Buildings, roads and water from OpenFreeMap vector tiles © OpenMapTiles",
  "Map tiles: OpenFreeMap © OpenMapTiles Data from OpenStreetMap",
  "Demo routes computed with OSRM from OpenStreetMap data",
  "Shadows computed for the sun at 1:45pm on October 24",
  "3D drawn with deck.gl. Fonts Overpass and Overpass Mono, SIL Open Font License",
];

export default function About() {
  usePageColors();
  const navigate = useNavigate();
  return (
    <div className="lp-root min-h-screen" data-testid="about-page">
      <header className="lp-masthead">
        <Link to="/" className="lp-focus flex h-full items-center" aria-label="Drivepast home" data-testid="about-home-link">
          <Wordmark testid="about-wordmark" />
        </Link>
        <div className="flex items-center gap-2">
          <Link to="/signin" className="lp-btn lp-btn-secondary lp-focus" data-testid="about-signin-link">
            Sign in
          </Link>
          <button type="button" onClick={() => navigate("/signin")} className="lp-btn lp-btn-primary lp-focus" data-testid="about-demo-link">
            Open the demo
          </button>
        </div>
      </header>
      <main className="px-[clamp(12px,3.4vw,52px)] pb-24 pt-[120px]">
        <div className="lp-sheet static w-full max-w-[720px]">
          <div className="lp-sheet-head">
            <span className="lp-sheet-num">i</span>
            <span className="flex-1 px-3">About and credits</span>
            <span className="pr-3 text-[#5C5A54]">Demo data</span>
          </div>
          <div className="lp-sheet-body">
            <h1 className="lp-h2" data-testid="about-title">
              About and credits
            </h1>
            <p className="lp-p">
              Drivepast prices each new stop from the van that already drives past. Bayline Courier and the Emeryville lab on the landing page are a fictional demo fleet.
            </p>
            <ul className="lp-rows" data-testid="about-credits-list">
              {CREDITS.map((c, i) => (
                <li key={c} className="lp-row justify-start" data-testid={`about-credit-${i + 1}`}>
                  {c}
                </li>
              ))}
            </ul>
            <div className="mt-6">
              <Link to="/" className="lp-btn lp-btn-secondary lp-focus" data-testid="about-back-link">
                Back to the story
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
