import { useEffect, useState } from "react";
import { Sun } from "lucide-react";
import { useFleet } from "@/context/FleetContext";
import { http } from "@/lib/api";

export const MorningBrief = () => {
  const { version } = useFleet();
  const [brief, setBrief] = useState(null);
  useEffect(() => {
    http.get("/brief").then(({ data }) => setBrief(data)).catch(() => setBrief(null));
  }, [version]);
  if (!brief) return null;
  const late = brief.most_late;
  const lateShare = late.total_runs ? Math.round((100 * late.late_runs) / late.total_runs) : 0;
  return (
    <section className="border border-[var(--dp-line)] bg-[var(--dp-surface)] px-4 py-3" data-testid="morning-brief">
      <p className="flex items-center gap-2 font-display text-sm font-semibold">
        <Sun size={15} aria-hidden="true" /> Morning brief
      </p>
      <ul className="mt-2 space-y-1 text-sm" data-testid="morning-brief-spare">
        {brief.vans.map((v) => (
          <li key={v.key} className="flex items-center gap-2" data-testid={`morning-brief-van-${v.key}`}>
            <span className="h-2 w-2" style={{ background: v.color }} />
            <span className="font-medium">{v.name}</span>
            <span className="text-[var(--dp-ink-2)]">{v.spare_minutes} spare min today</span>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-sm text-[var(--dp-ink-2)]" data-testid="morning-brief-late">
        <span className="font-medium text-[var(--dp-ink)]">{late.name}</span> runs late most often. {late.late_runs} of its last {late.total_runs}
        stops ({lateShare}%) came in over {brief.late_after_plan_minutes} min behind plan.
      </p>
    </section>
  );
};
