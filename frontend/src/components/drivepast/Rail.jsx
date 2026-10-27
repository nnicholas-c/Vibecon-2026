import { Brain, Check, ChevronsUpDown, History, Inbox, Settings, Smartphone, Truck } from "lucide-react";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { useFleet } from "@/context/FleetContext";

function BusinessSwitcher({ name }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="flex w-full items-center justify-between rounded-lg border border-[var(--dp-line)] bg-[var(--dp-bg)] px-3 py-2.5 text-left transition-colors hover:border-white/25"
        data-testid="business-switcher-trigger"
      >
        <span className="min-w-0">
          <span className="block text-[11px] uppercase tracking-wider text-[var(--dp-ink-3)]">Business</span>
          <span className="block truncate font-display text-sm font-semibold" data-testid="business-name">{name}</span>
        </span>
        <ChevronsUpDown className="h-4 w-4 text-[var(--dp-ink-3)]" />
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-[228px]" align="start" data-testid="business-switcher-menu">
        <DropdownMenuLabel className="text-xs text-[var(--dp-ink-3)]">Your businesses</DropdownMenuLabel>
        <DropdownMenuItem className="justify-between" data-testid="business-switcher-option-bayline">
          {name}
          <Check className="h-4 w-4 text-[var(--dp-green)]" />
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function RailRow({ active, onClick, testId, children }) {
  return (
    <button
      onClick={onClick}
      data-testid={testId}
      aria-current={active ? "page" : undefined}
      className={`group flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors ${
        active ? "bg-[var(--dp-green-soft)]" : "hover:bg-[var(--dp-bg)]"
      }`}
    >
      {children}
    </button>
  );
}

function UnitRow({ unit, active, onClick }) {
  const k = unit.key;
  return (
    <RailRow active={active} onClick={onClick} testId={`rail-unit-row-${k}`}>
      <span className="mt-0.5 h-2.5 w-2.5 shrink-0 self-start rounded-full ring-4 ring-white" style={{ background: unit.color }} data-testid={`rail-unit-dot-${k}`} />
      <span className="min-w-0 flex-1">
        <span className="flex items-baseline gap-1.5">
          <span className="font-medium" data-testid={`rail-unit-name-${k}`}>{unit.name}</span>
          <span className="truncate text-xs text-[var(--dp-ink-2)]" data-testid={`rail-unit-nickname-${k}`}>{unit.nickname}</span>
        </span>
        <span className="tnum block text-xs text-[var(--dp-ink-3)]" data-testid={`rail-unit-status-${k}`}>
          {unit.stops_count} stops, {unit.spare_minutes} spare min
        </span>
      </span>
    </RailRow>
  );
}

function BottomLinks({ view, inbox, onNavigate }) {
  const { phonesOpen, setPhonesOpen } = useFleet();
  return (
    <div className="space-y-0.5 border-t border-[var(--dp-line)] px-3 py-3">
      <RailRow active={view === "inbox"} onClick={() => onNavigate("/inbox")} testId="rail-inbox-link">
        <Inbox className="h-4 w-4 text-[var(--dp-ink-2)]" />
        <span className="flex-1 text-sm font-medium">Inbox</span>
        <span className="tnum rounded-full bg-[var(--dp-accent)] px-2 py-0.5 text-xs font-semibold text-[var(--dp-ink)]" data-testid="rail-inbox-count">
          {inbox ?? 0}
        </span>
      </RailRow>
      <RailRow active={view === "memory"} onClick={() => onNavigate("/memory")} testId="rail-memory-link">
        <Brain className="h-4 w-4 text-[var(--dp-ink-2)]" />
        <span className="text-sm font-medium">Memory</span>
      </RailRow>
      <RailRow active={view === "activity"} onClick={() => onNavigate("/activity")} testId="rail-activity-link">
        <History className="h-4 w-4 text-[var(--dp-ink-2)]" />
        <span className="text-sm font-medium">Activity</span>
      </RailRow>
      <RailRow active={view === "settings"} onClick={() => onNavigate("/settings")} testId="rail-settings-link">
        <Settings className="h-4 w-4 text-[var(--dp-ink-2)]" />
        <span className="text-sm font-medium">Settings</span>
      </RailRow>
      <RailRow active={phonesOpen} onClick={() => { onNavigate("/dispatch"); setPhonesOpen(true); }} testId="rail-phones-link">
        <Smartphone className="h-4 w-4 text-[var(--dp-ink-2)]" />
        <span className="text-sm font-medium">Demo phones</span>
      </RailRow>
    </div>
  );
}

function OwnerCorner({ name }) {
  const initials = (name || "").split(" ").map((p) => p[0]).join("").slice(0, 2);
  return (
    <div className="flex items-center gap-3 border-t border-[var(--dp-line)] px-5 py-3" data-testid="owner-corner">
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--dp-accent)] text-xs font-semibold text-[var(--dp-ink)]">{initials}</span>
      <span className="min-w-0">
        <span className="block truncate text-sm font-medium" data-testid="owner-name">{name}</span>
        <span className="block text-xs text-[var(--dp-ink-3)]">Owner</span>
      </span>
    </div>
  );
}

export default function Rail({ view, unitKey, onNavigate }) {
  const { fleet, error } = useFleet();
  const units = fleet?.units || [];
  return (
    <div className="flex min-h-0 flex-1 flex-col" data-testid="left-rail">
      <div className="space-y-3 px-4 pb-3 pt-5">
        <p className="hidden font-display text-lg font-bold tracking-tight md:block" data-testid="app-wordmark">Drivepast</p>
        <BusinessSwitcher name={fleet?.business?.name || "Bayline Courier"} />
      </div>
      <nav className="dp-scroll min-h-0 flex-1 space-y-0.5 overflow-y-auto px-3" data-testid="rail-nav">
        <RailRow active={view === "dispatch"} onClick={() => onNavigate("/dispatch")} testId="rail-dispatch-row">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--dp-accent)] text-[var(--dp-ink)]" data-testid="rail-dispatch-icon">
            <Truck className="h-4 w-4" />
          </span>
          <span className="min-w-0">
            <span className="block font-medium">Fleet</span>
            <span className="block text-xs text-[var(--dp-ink-3)]">Whole fleet{units.length ? `, ${units.length} vans` : ""}</span>
          </span>
        </RailRow>
        <p className="px-3 pb-1 pt-4 text-[11px] font-medium uppercase tracking-wider text-[var(--dp-ink-3)]">Vans</p>
        {!fleet && !error && [0, 1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="mx-3 my-2 h-10 rounded-lg" />)}
        {!fleet && error && <p className="px-3 py-2 text-sm text-[var(--dp-ink-2)]" data-testid="rail-offline">Vans show up here once Drivepast is back online.</p>}
        {units.map((u) => (
          <UnitRow key={u.key} unit={u} active={view === "unit" && unitKey === u.key} onClick={() => onNavigate(`/units/${u.key}`)} />
        ))}
      </nav>
      <BottomLinks view={view} inbox={fleet?.inbox_new_count} onNavigate={onNavigate} />
      <OwnerCorner name={fleet?.business?.owner_name || "Rosa Delgado"} />
    </div>
  );
}
