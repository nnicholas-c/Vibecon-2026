import { WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useFleet } from "@/context/FleetContext";

export function OfflineBanner({ message }) {
  const { reload } = useFleet();
  return (
    <div
      className="flex items-center justify-between gap-3 border-b border-[var(--dp-amber)] bg-[var(--dp-amber-soft)] px-4 py-2.5 text-sm text-[var(--dp-amber)]"
      data-testid="offline-banner"
      role="alert"
    >
      <span className="flex items-center gap-2">
        <WifiOff className="h-4 w-4 shrink-0" />
        <span data-testid="offline-message">{message}</span>
      </span>
      <Button size="sm" variant="outline" className="h-8 rounded-lg bg-[var(--dp-surface)]" onClick={reload} data-testid="offline-retry-button">
        Try again
      </Button>
    </div>
  );
}

export function FriendlyNotice({ title, message, onRetry, testId = "friendly-notice" }) {
  return (
    <div className="dp-card mx-auto my-10 max-w-md p-8 text-center" data-testid={testId}>
      <p className="font-display text-lg font-semibold">{title}</p>
      <p className="mt-2 text-sm text-[var(--dp-ink-2)]">{message}</p>
      {onRetry && (
        <Button className="mt-5 rounded-lg" onClick={onRetry} data-testid={`${testId}-retry`}>
          Try again
        </Button>
      )}
    </div>
  );
}
