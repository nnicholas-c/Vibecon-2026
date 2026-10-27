export function Section({ title, note, children, testId, id }) {
  return (
    <section id={id} className="dp-card scroll-mt-6 p-5 sm:p-6" data-testid={testId}>
      <h2 className="text-base font-semibold md:text-lg">{title}</h2>
      {note && <p className="mt-1 text-sm text-[var(--dp-ink-2)]">{note}</p>}
      <div className="mt-5">{children}</div>
    </section>
  );
}

export function NumberField({ field, value, error, onChange }) {
  const id = `settings-${field.key}`;
  return (
    <div className="min-w-0">
      <label htmlFor={id} className="text-sm font-medium">{field.label}</label>
      <div
        className={`mt-1.5 flex h-11 items-center rounded-lg border bg-[var(--dp-surface)] px-3 transition-colors focus-within:border-[var(--dp-green)] ${
          error ? "border-[var(--dp-amber)]" : "border-[var(--dp-line)]"
        }`}
      >
        {field.prefix && <span className="pr-1 text-sm text-[var(--dp-ink-3)]">{field.prefix}</span>}
        <input
          id={id}
          value={value}
          onChange={(e) => onChange(field.key, e.target.value)}
          inputMode="decimal"
          aria-invalid={Boolean(error)}
          data-testid={`${id}-input`}
          className="tnum h-full min-w-0 flex-1 bg-transparent text-sm outline-none"
        />
        {field.suffix && <span className="shrink-0 pl-2 text-xs text-[var(--dp-ink-3)]">{field.suffix}</span>}
      </div>
      {error ? (
        <p className="mt-1 text-xs font-medium text-[var(--dp-amber)]" data-testid={`${id}-error`} role="alert">{error}</p>
      ) : (
        field.hint && <p className="mt-1 text-xs text-[var(--dp-ink-3)]">{field.hint}</p>
      )}
    </div>
  );
}

export function ReadOnlyRow({ label, value, testId }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg bg-[var(--dp-bg)] px-4 py-3">
      <span className="text-sm text-[var(--dp-ink-2)]">{label}</span>
      <span className="tnum text-sm font-medium" data-testid={testId}>{value}</span>
    </div>
  );
}
