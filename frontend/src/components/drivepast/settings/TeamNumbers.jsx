import { useState } from "react";
import { Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { checkPhone } from "./config";

export function TeamNumbers({ numbers, onChange, error }) {
  const [draft, setDraft] = useState("");
  const [draftError, setDraftError] = useState("");
  const add = () => {
    const msg = checkPhone(draft);
    if (!msg && numbers.length >= 10) return setDraftError("You can add up to 10 numbers.");
    if (msg) return setDraftError(msg);
    onChange([...numbers, draft.trim()]);
    setDraft("");
    setDraftError("");
  };
  return (
    <div data-testid="team-numbers">
      <p className="text-sm font-medium">Team numbers</p>
      <p className="mt-0.5 text-xs text-[var(--dp-ink-3)]">If real texting is ever turned on, texts only go to these numbers.</p>
      {numbers.length === 0 ? (
        <p className="mt-3 text-sm text-[var(--dp-ink-2)]" data-testid="team-numbers-empty">No team numbers yet.</p>
      ) : (
        <ul className="mt-3 space-y-2" data-testid="team-numbers-list">
          {numbers.map((n, i) => (
            <li key={`${n}-${i}`} className="flex items-center justify-between rounded-lg bg-[var(--dp-bg)] px-4 py-2.5" data-testid={`team-number-item-${i}`}>
              <span className="tnum text-sm">{n}</span>
              <button
                type="button"
                onClick={() => onChange(numbers.filter((_, j) => j !== i))}
                className="rounded-full p-1 text-[var(--dp-ink-3)] transition-colors hover:bg-[var(--dp-surface)] hover:text-[var(--dp-ink)]"
                aria-label={`Remove ${n}`}
                data-testid={`team-number-remove-${i}`}
              >
                <X className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="mt-3 flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), add())}
          placeholder="(510) 555-0199"
          inputMode="tel"
          data-testid="team-number-input"
          className="tnum h-11 min-w-0 flex-1 rounded-lg border border-[var(--dp-line)] bg-[var(--dp-surface)] px-3 text-sm outline-none focus:border-[var(--dp-green)]"
        />
        <Button type="button" variant="outline" className="h-11 rounded-lg" onClick={add} data-testid="team-number-add-button">
          <Plus className="mr-1 h-4 w-4" /> Add
        </Button>
      </div>
      {(draftError || error) && <p className="mt-1 text-xs font-medium text-[var(--dp-amber)]" data-testid="team-number-error">{draftError || error}</p>}
    </div>
  );
}
