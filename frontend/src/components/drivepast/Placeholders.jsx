import { Inbox, Smartphone } from "lucide-react";
import { useFleet } from "@/context/FleetContext";

function Placeholder({ icon: Icon, title, message, testId }) {
  return (
    <div className="mx-auto w-full max-w-xl p-6 md:p-10" data-testid={testId}>
      <div className="dp-card dp-rise p-8 sm:p-10">
        <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--dp-green-soft)] text-[var(--dp-green)]">
          <Icon className="h-6 w-6" />
        </span>
        <h1 className="mt-6 text-2xl font-bold tracking-tight" data-testid={`${testId}-title`}>{title}</h1>
        <p className="mt-3 text-base text-[var(--dp-ink-2)]" data-testid={`${testId}-message`}>{message}</p>
      </div>
    </div>
  );
}

export function InboxPlaceholder() {
  const { fleet } = useFleet();
  const n = fleet?.inbox_new_count ?? 0;
  return (
    <Placeholder
      icon={Inbox}
      title={`You have ${n} new ${n === 1 ? "request" : "requests"}`}
      message="The inbox opens in a later step. Your requests are saved and waiting."
      testId="inbox-placeholder"
    />
  );
}

export function PhonesPlaceholder() {
  return (
    <Placeholder
      icon={Smartphone}
      title="Demo phones"
      message="Demo phones arrive in a later step."
      testId="phones-placeholder"
    />
  );
}
