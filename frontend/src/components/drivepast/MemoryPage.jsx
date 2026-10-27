import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import { friendlyMessage, http } from "@/lib/api";

const SAVE_FAIL = "Couldn't save that rule. Try again.";

function RuleChip({ rule, onToggle, onDelete, busy }) {
  const id = `memory-rule-${rule.id}`;
  return (
    <li className="dp-rise flex items-start gap-4 border border-[var(--dp-ink)] bg-[var(--dp-surface)] px-4 py-3" data-testid={id}>
      <div className="min-w-0 flex-1">
        <p className="text-base font-semibold" data-testid={`${id}-text`}>{rule.text}</p>
        <p className="mt-1 font-mono text-xs uppercase tracking-wider text-[var(--dp-ink-3)]" data-testid={`${id}-kind`}>
          {rule.enforced ? rule.enforced_line : "Assistant instruction"}
        </p>
      </div>
      <div className="flex items-center gap-3">
        <span className="font-mono text-xs uppercase text-[var(--dp-ink-3)]" data-testid={`${id}-state`}>{rule.active ? "On" : "Off"}</span>
        <Switch checked={rule.active} disabled={busy} onCheckedChange={(v) => onToggle(rule, v)} aria-label={`Turn ${rule.active ? "off" : "on"} rule`} data-testid={`${id}-switch`} />
        <button onClick={() => onDelete(rule)} disabled={busy} aria-label="Delete rule" data-testid={`${id}-delete`}
          className="flex h-9 w-9 items-center justify-center border border-[var(--dp-line)] transition-colors hover:border-[var(--dp-ink)] disabled:opacity-50">
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </li>
  );
}

export default function MemoryPage() {
  const [rules, setRules] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  const load = async () => {
    try {
      const { data } = await http.get("/memory/rules");
      setRules(data.rules);
      setError("");
    } catch (err) {
      setError(friendlyMessage(err, "Couldn't load your rules. Try again."));
    }
  };
  useEffect(() => { load(); }, []);

  const toggle = async (rule, active) => {
    setBusy(rule.id);
    setRules((rs) => rs.map((r) => (r.id === rule.id ? { ...r, active } : r)));
    try {
      await http.patch(`/memory/rules/${rule.id}`, { active });
    } catch {
      setRules((rs) => rs.map((r) => (r.id === rule.id ? { ...r, active: rule.active } : r)));
      toast.error(SAVE_FAIL);
    }
    setBusy("");
  };

  const remove = async (rule) => {
    setBusy(rule.id);
    try {
      await http.delete(`/memory/rules/${rule.id}`);
      setRules((rs) => rs.filter((r) => r.id !== rule.id));
    } catch {
      toast.error(SAVE_FAIL);
    }
    setBusy("");
  };

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6 p-4 md:p-8" data-testid="memory-page">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight" data-testid="memory-title">Memory</h1>
        <p className="mt-2 text-sm text-[var(--dp-ink-2)]">
          Rules you told the assistant. Rules like "Don't send Van 2 downtown after 3" also keep that van out of the options.
        </p>
      </div>
      {error && <p className="text-sm text-[var(--dp-red)]" data-testid="memory-error">{error}</p>}
      {!rules && !error && <Skeleton className="h-16 w-full" />}
      {rules && rules.length === 0 && (
        <p className="border border-[var(--dp-line)] bg-[var(--dp-surface)] px-4 py-6 text-sm text-[var(--dp-ink-2)]" data-testid="memory-empty">
          No rules yet. Tell the assistant one in the chat, like "Never send Van 1 to SF after 3pm".
        </p>
      )}
      {rules && rules.length > 0 && (
        <ul className="space-y-3" data-testid="memory-rule-list">
          {rules.map((r) => <RuleChip key={r.id} rule={r} onToggle={toggle} onDelete={remove} busy={busy === r.id} />)}
        </ul>
      )}
    </div>
  );
}
