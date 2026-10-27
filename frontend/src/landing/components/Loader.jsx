import { Wordmark } from "./Mark";

function LoadRow({ label, value, ready, testid }) {
  return (
    <div className="lp-load-row" data-testid={testid}>
      <span>{label}</span>
      <span className={ready ? "opacity-100" : "opacity-[0.32]"} data-testid={`${testid}-value`}>
        {ready ? value.toLocaleString("en-US") : "..."}
      </span>
    </div>
  );
}

export default function Loader({ counts, ready, progress, leaving, reduced }) {
  const c = counts || { streets: 10526, buildings: 56364, vans: 3, stops: 16 };
  const out = leaving ? (reduced ? "lp-loader-fade" : "lp-loader-up") : "";
  return (
    <div className={`lp-loader ${out}`} role="status" aria-live="polite" aria-label="Loading the 3D model" data-testid="landing-loader">
      <div className="flex items-center justify-between">
        <Wordmark testid="landing-loader-wordmark" />
        <span className="lp-label text-[#5C5A54]">Demo data</span>
      </div>
      <div className="w-full max-w-[720px]">
        <p className="lp-loader-title">Building the Bay Area from real streets.</p>
        <div className="mt-8">
          <LoadRow label="Street segments" value={c.streets} ready={ready.roads} testid="landing-loader-streets" />
          <LoadRow label="Buildings" value={c.buildings} ready={ready.buildings} testid="landing-loader-buildings" />
          <LoadRow label="Vans" value={c.vans} ready={ready.fleet} testid="landing-loader-vans" />
          <LoadRow label="Stops today" value={c.stops} ready={ready.fleet} testid="landing-loader-stops" />
        </div>
      </div>
      <div className="h-[2px] w-full bg-[#CFCBC2]" data-testid="landing-loader-track">
        <div className="h-full bg-[#141414] transition-[width] duration-200" style={{ width: `${Math.round(progress * 100)}%` }} />
      </div>
    </div>
  );
}

export function ErrorNote() {
  return (
    <div className="lp-error" role="alert" data-testid="landing-error-note">
      {"The 3D view couldn't start on this device, so here's the story without it."}
    </div>
  );
}
