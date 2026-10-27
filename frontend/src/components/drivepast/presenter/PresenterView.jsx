import { useFleet } from "@/context/FleetContext";
import { FleetMap } from "../Maps";
import { Phone, usePhones } from "../DemoPhones";

export default function PresenterView() {
  const { live } = useFleet();
  const demo = live?.demo;
  const { data, busy: phoneBusy, act, reply } = usePhones(true);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-2 p-2" data-testid="presenter-view">
      {!demo && <p className="border border-[var(--dp-amber)] bg-[var(--dp-amber-soft)] px-3 py-2 text-sm text-[var(--dp-amber)]" data-testid="presenter-not-running">The demo isn't running. Reset the demo data to start it.</p>}
      {demo?.request?.flag && <p className="border border-[var(--dp-amber)] bg-[var(--dp-amber-soft)] px-3 py-2 text-sm text-[var(--dp-amber)]" data-testid="presenter-held">Held for you: {demo.request.flag}</p>}
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-2 lg:grid-cols-[minmax(0,1fr)_300px_300px]">
        <div className="dp-frame dp-scroll min-h-0 overflow-y-auto bg-[var(--dp-page)] p-4" data-testid="presenter-map"><FleetMap /></div>
        <Phone id="driver" title="Driver" messages={data.driver || []} onAct={act} onReply={reply} busy={phoneBusy} height="h-[640px] lg:h-full" />
        <Phone id="customer" title="Customer" messages={data.customer || []} onAct={act} onReply={reply} busy={phoneBusy} height="h-[640px] lg:h-full" />
      </div>
    </div>
  );
}
