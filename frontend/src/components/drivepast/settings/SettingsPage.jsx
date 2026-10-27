import { useCallback, useEffect, useState } from "react";
import { Check } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { useFleet } from "@/context/FleetContext";
import { friendlyMessage, http } from "@/lib/api";
import { fmtTime } from "@/lib/format";
import { FriendlyNotice } from "../Offline";
import { CLOCK_OPTIONS, NUMBER_KEYS, NUMBER_SECTIONS, checkNumber, displayNumber } from "./config";
import { Connections, DemoControls } from "./Controls";
import { EmailGoogle } from "./EmailGoogle";
import { NumberField, ReadOnlyRow, Section } from "./Fields";
import { TeamNumbers } from "./TeamNumbers";
import EngineTest from "./EngineTest";

function toForm(s) {
  const form = { auto_send_cheapest: s.auto_send_cheapest, demo_clock_minutes: s.demo_clock_minutes, texting_channel: s.texting_channel, team_numbers: [...s.team_numbers] };
  NUMBER_KEYS.forEach((f) => { form[f.key] = displayNumber(f, s[f.key]); });
  return form;
}

function validate(form) {
  const errors = {};
  NUMBER_KEYS.forEach((f) => {
    const msg = checkNumber(f.key, form[f.key]);
    if (msg) errors[f.key] = msg;
  });
  if (!errors.market_ref_low && !errors.market_ref_high && Number(form.market_ref_low) > Number(form.market_ref_high)) {
    errors.market_ref_high = "The high end must be at least the low end.";
  }
  [["floor_recurring", "usual_recurring", "a visit"], ["floor_one_off", "usual_one_off", "for the run"]].forEach(([fl, us, what]) => {
    if (!errors[fl] && !errors[us] && Number(form[fl]) > Number(form[us])) errors[fl] = `Your floor can't be above your usual price of $${Number(form[us])} ${what}.`;
  });
  return errors;
}

function Select({ value, onChange, options, testId }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      data-testid={testId}
      className="tnum h-11 w-full rounded-lg border border-[var(--dp-line)] bg-[var(--dp-surface)] px-3 text-sm outline-none focus:border-[var(--dp-green)]"
    >
      {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function SendingSection({ form, set }) {
  return (
    <Section title="Sending" testId="settings-sending" id="auto-send">
      <div className="flex items-center justify-between gap-4">
        <span>
          <span className="block text-sm font-medium">Demo mode: auto-send the cheapest option within my rules</span>
          <span className="block text-xs text-[var(--dp-ink-3)]">When on, the Cheapest option goes out as soon as a request is priced, if it's at or above your floor and doesn't lose money.</span>
        </span>
        <Switch checked={form.auto_send_cheapest} onCheckedChange={(v) => set("auto_send_cheapest", v)} data-testid="settings-auto-send-switch" />
      </div>
    </Section>
  );
}

function DemoClockSection({ form, set, meta }) {
  const opts = CLOCK_OPTIONS.includes(form.demo_clock_minutes) ? CLOCK_OPTIONS : [...CLOCK_OPTIONS, form.demo_clock_minutes].sort((a, b) => a - b);
  return (
    <Section title="Demo date and clock" note="The app treats this as 'now'. The date stays fixed until the next reset." testId="settings-demo-clock">
      <div className="space-y-4">
        <ReadOnlyRow label="Demo date (treated as a weekday)" value={meta.demo_date_label} testId="settings-demo-date" />
        <div>
          <label className="text-sm font-medium" htmlFor="demo-clock">Demo clock</label>
          <div className="mt-1.5" id="demo-clock">
            <Select value={form.demo_clock_minutes} onChange={(v) => set("demo_clock_minutes", Number(v))} options={opts.map((m) => ({ value: m, label: fmtTime(m) }))} testId="settings-demo-clock-select" />
          </div>
        </div>
      </div>
    </Section>
  );
}

function TextingSection({ form, set, errors }) {
  return (
    <Section title="Texting" testId="settings-texting">
      <div className="space-y-4">
        <ReadOnlyRow label="Real texting" value="Off" testId="settings-real-texting-status" />
        <div>
          <label className="text-sm font-medium">Channel</label>
          <div className="mt-1.5">
            <Select value={form.texting_channel} onChange={(v) => set("texting_channel", v)} options={[{ value: "sms", label: "SMS" }, { value: "whatsapp", label: "WhatsApp sandbox" }]} testId="settings-texting-channel-select" />
          </div>
        </div>
        <TeamNumbers numbers={form.team_numbers} onChange={(v) => set("team_numbers", v)} error={errors.team_numbers} />
      </div>
    </Section>
  );
}

export default function SettingsPage() {
  const { reload } = useFleet();
  const [meta, setMeta] = useState(null);
  const [form, setForm] = useState(null);
  useEffect(() => {
    if (!form || !window.location.hash) return;
    document.getElementById(window.location.hash.slice(1))?.scrollIntoView({ block: "start" });
  }, [form]);
  const [errors, setErrors] = useState({});
  const [loadError, setLoadError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);
  const [tab, setTab] = useState("main");

  const load = useCallback(async () => {
    try {
      const { data } = await http.get("/settings");
      setMeta(data);
      setForm(toForm(data.settings));
      setErrors({});
      setLoadError("");
    } catch (err) {
      setLoadError(friendlyMessage(err, "Couldn't load Settings. Try again in a moment."));
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const set = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }));
    setErrors((e) => ({ ...e, [key]: "" }));
    setSaveMsg(null);
  };

  const save = async () => {
    const found = validate(form);
    setErrors(found);
    if (Object.values(found).some(Boolean)) {
      setSaveMsg({ ok: false, text: "Some values need fixing. Nothing was saved." });
      return;
    }
    setSaving(true);
    const patch = { ...form };
    NUMBER_KEYS.forEach((f) => { patch[f.key] = Number(form[f.key]); });
    try {
      const { data } = await http.put("/settings", patch);
      setMeta(data);
      setForm(toForm(data.settings));
      setSaveMsg({ ok: true, text: data.recomputed ? "Saved. Routes re-timed." : "Saved" });
      toast.success("Saved");
      reload();
    } catch (err) {
      const fields = err?.response?.data?.detail?.fields;
      if (fields) setErrors(fields);
      setSaveMsg({ ok: false, text: fields ? "Some values need fixing. Nothing was saved." : friendlyMessage(err, "Couldn't save. Try again.") });
    } finally {
      setSaving(false);
    }
  };

  if (loadError) return <FriendlyNotice title="Settings didn't load" message={loadError} onRetry={load} testId="settings-error" />;
  if (!form) return <div className="space-y-4 p-6 md:p-10"><Skeleton className="h-64 rounded-2xl" /><Skeleton className="h-64 rounded-2xl" /></div>;

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6 p-4 pb-28 sm:p-6 sm:pb-28 md:p-10 md:pb-28" data-testid="settings-page">
      <div>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">Settings</h1>
        <p className="mt-1 text-sm text-[var(--dp-ink-2)]">Set your rules once. The van agents stick to them.</p>
      </div>
      <div className="flex gap-1 rounded-lg bg-[var(--dp-card)] p-1 sm:w-fit" role="tablist">
        {[["main", "Settings"], ["engine", "Engine test"]].map(([k, label]) => (
          <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)} data-testid={`settings-tab-${k}`}
            className={`flex-1 whitespace-nowrap rounded-md px-5 py-2 text-sm font-medium transition-colors ${tab === k ? "bg-[var(--dp-ink)] text-[var(--dp-page)]" : "text-[var(--dp-ink-2)] hover:bg-[var(--dp-bg)]"}`}>
            {label}
          </button>
        ))}
      </div>
      {tab === "engine" ? <EngineTest /> : (<>
      {NUMBER_SECTIONS.map((sec) => (
        <Section key={sec.title} title={sec.title} note={sec.note} testId={`settings-section-${sec.fields[0].key}`}>
          <div className="grid grid-cols-1 gap-x-5 gap-y-4 sm:grid-cols-2">
            {sec.fields.map((f) => <NumberField key={f.key} field={f} value={form[f.key]} error={errors[f.key]} onChange={set} />)}
          </div>
        </Section>
      ))}
      <SendingSection form={form} set={set} />
      <DemoClockSection form={form} set={set} meta={meta} />
      <TextingSection form={form} set={set} errors={errors} />
      <Section title="Business" testId="settings-business">
        <ReadOnlyRow label="Business type" value={meta.business_type_label} testId="settings-business-type" />
      </Section>
      <EmailGoogle />
      <Connections rows={meta.connections} />
      <DemoControls onReset={async () => { await load(); await reload(); setSaveMsg(null); }} />
      <div className="sticky bottom-4 z-20">
        <div className="dp-card flex items-center justify-between gap-3 px-4 py-3">
          <span className={`text-sm font-medium ${saveMsg?.ok ? "text-[var(--dp-green)]" : "text-[var(--dp-amber)]"}`} data-testid="settings-save-status" role="status">
            {saveMsg?.ok && <Check className="mr-1 inline h-4 w-4" />}
            {saveMsg?.text || ""}
          </span>
          <Button onClick={save} disabled={saving} className="h-11 rounded-lg px-6 font-semibold tracking-wide" data-testid="settings-save-button">
            {saving ? "Saving..." : "Save settings"}
          </Button>
        </div>
      </div>
      </>)}
    </div>
  );
}
