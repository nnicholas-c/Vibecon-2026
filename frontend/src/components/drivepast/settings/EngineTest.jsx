import { useEffect, useState } from "react";
import { Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { friendlyMessage, http } from "@/lib/api";
import { RequestResult } from "./EngineResult";
import { WhatIf } from "./WhatIf";

const SOURCE = { email: "Email", text: "Text", pdf: "PDF", voicemail: "Voicemail", photo: "Photo" };

function JobCard({ job, result }) {
  const n = job.number;
  const ready = job.job_status === "ready";
  return (
    <div className="dp-card p-5 sm:p-6" data-testid={`engine-request-${n}`}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-display text-base font-semibold">Request {n}</span>
        <span className="rounded-full bg-[var(--dp-bg)] px-2 py-0.5 text-xs text-[var(--dp-ink-2)]">{SOURCE[job.source] || job.source}</span>
        <span className="text-sm text-[var(--dp-ink-2)]">{job.sender}</span>
        {!ready && <span className="rounded-full bg-[var(--dp-amber-soft)] px-2 py-0.5 text-xs font-medium text-[var(--dp-amber)]" data-testid={`engine-cant-price-${n}`}>Can't price yet</span>}
      </div>
      <p className="mt-2 text-sm" data-testid={`engine-summary-${n}`}>{ready ? job.job_summary : job.job_reason}</p>
      {ready && job.job?.notes && <p className="mt-1 text-xs text-[var(--dp-ink-3)]">{job.job.notes}</p>}
      {ready && result && <div className="mt-4"><RequestResult res={result} /></div>}
    </div>
  );
}

export default function EngineTest() {
  const [jobs, setJobs] = useState(null);
  const [results, setResults] = useState({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    http.get("/engine/jobs").then(({ data }) => setJobs(data)).catch((err) => setError(friendlyMessage(err, "Couldn't load the requests. Try again.")));
  }, []);

  const runAll = async () => {
    setBusy(true);
    setError("");
    try {
      const { data } = await http.post("/engine/run-all", {}, { timeout: 30000 });
      setResults(Object.fromEntries(data.results.map((r) => [r.request_key, r])));
    } catch (err) {
      setError(friendlyMessage(err, "The engine hit a problem on this request. Try again."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="engine-test">
      <div className="dp-card flex flex-wrap items-center justify-between gap-4 p-5 sm:p-6">
        <div>
          <h2 className="text-base font-semibold md:text-lg">Engine test</h2>
          <p className="mt-1 text-sm text-[var(--dp-ink-2)]">Prices every seeded request on all three vans. It never changes a route.</p>
        </div>
        <Button className="h-11 rounded-lg px-6 font-semibold tracking-wide" onClick={runAll} disabled={busy || !jobs} data-testid="engine-run-all-button">
          <Play className="mr-2 h-4 w-4" />{busy ? "Running..." : "Run all"}
        </Button>
      </div>
      {error && <p className="text-sm text-[var(--dp-amber)]" data-testid="engine-test-error">{error}</p>}
      {!jobs && !error && <Skeleton className="h-64 rounded-2xl" />}
      {(jobs || []).map((j) => <JobCard key={j.request_key} job={j} result={results[j.request_key]} />)}
      <WhatIf />
    </div>
  );
}
