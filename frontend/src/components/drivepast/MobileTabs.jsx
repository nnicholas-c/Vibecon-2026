import { List, MessageSquare, PanelRight } from "lucide-react";
import { useFleet } from "@/context/FleetContext";

const TABS = [
  { key: "list", label: "List", icon: List },
  { key: "chat", label: "Chat", icon: MessageSquare },
  { key: "page", label: "Page", icon: PanelRight },
];

export function MobileTabs({ tab, onChange }) {
  const { fleet } = useFleet();
  return (
    <div className="border-b border-[var(--dp-line)] bg-[var(--dp-surface)] md:hidden" data-testid="mobile-header">
      <div className="flex items-center justify-between px-4 pt-3">
        <span className="font-display text-base font-bold tracking-tight">Drivepast</span>
        <span className="truncate pl-3 text-xs text-[var(--dp-ink-2)]" data-testid="mobile-owner-name">
          {fleet?.business?.owner_name ? `${fleet.business.owner_name}, Owner` : ""}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-1 px-3 pb-2 pt-2" role="tablist">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            role="tab"
            aria-selected={tab === key}
            onClick={() => onChange(key)}
            data-testid={`mobile-tab-${key}`}
            className={`flex items-center justify-center gap-1.5 rounded-lg py-2 text-sm font-medium transition-colors ${
              tab === key ? "bg-[var(--dp-ink)] text-[var(--dp-page)]" : "text-[var(--dp-ink-2)] hover:bg-[var(--dp-bg)]"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
