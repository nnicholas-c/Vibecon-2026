import { useEffect, useState } from "react";
import { Plug } from "lucide-react";
import { Button } from "@/components/ui/button";
import { friendlyMessage, http } from "@/lib/api";
import { Section } from "./Fields";

const OPENAI_URL = "https://api.openai.com/v1";

function Input({ id, label, value, onChange, type = "text", placeholder, error }) {
  return (
    <div className="min-w-0">
      <label htmlFor={id} className="text-sm font-medium">{label}</label>
      <input id={id} type={type} value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} data-testid={`${id}-input`} autoComplete="off"
        className={`mt-1.5 h-11 w-full rounded-lg border bg-[var(--dp-surface)] px-3 text-sm outline-none focus:border-[var(--dp-green)] ${error ? "border-[var(--dp-amber)]" : "border-[var(--dp-line)]"}`} />
      {error && <p className="mt-1 text-xs font-medium text-[var(--dp-amber)]" data-testid={`${id}-error`}>{error}</p>}
    </div>
  );
}

function Pick({ id, label, value, options, onChange }) {
  return (
    <div className="min-w-0">
      <label htmlFor={id} className="text-sm font-medium">{label}</label>
      <select id={id} value={value} onChange={(e) => onChange(e.target.value)} data-testid={`${id}-select`}
        className="mt-1.5 h-11 w-full rounded-lg border border-[var(--dp-line)] bg-[var(--dp-surface)] px-3 text-sm outline-none focus:border-[var(--dp-green)]">
        {Object.entries(options).map(([k, name]) => <option key={k} value={k}>{name}</option>)}
      </select>
    </div>
  );
}

function LastAnswered({ a }) {
  if (!a) return <p className="text-sm text-[var(--dp-ink-3)]" data-testid="ai-last-answered">Last answered by: nothing yet</p>;
  const when = new Date(a.at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  const who = a.level === 3 ? a.model : `${a.label} · ${a.model}`;
  return <p className="tnum text-sm" data-testid="ai-last-answered">Last answered by: <span className="font-semibold">{who}</span> · {a.seconds.toFixed(1)} s · {when}</p>;
}

export function OurModel() {
  const [cfg, setCfg] = useState(null);
  const [form, setForm] = useState({ base_url: "", model: "", secret: "" });
  const [msg, setMsg] = useState("");
  const [errors, setErrors] = useState({});
  const [test, setTest] = useState(null);
  const [busy, setBusy] = useState("");

  const apply = (data) => { setCfg(data); setForm({ base_url: data.base_url, model: data.model, secret: "" }); setTest(data.last_test); };
  useEffect(() => { http.get("/ai/config").then(({ data }) => apply(data)).catch(() => setMsg("Couldn't load the model settings.")); }, []);
  const set = (k, v) => { setForm((f) => ({ ...f, [k]: v })); setErrors({}); setMsg(""); };

  const save = async (extra = {}) => {
    setBusy("save");
    try {
      const body = { base_url: form.base_url, model: form.model, ...extra };
      if (form.secret) body.secret = form.secret;
      const { data } = await http.put("/ai/config", body);
      apply(data);
      setMsg("Saved");
    } catch (err) {
      setErrors(err?.response?.data?.detail?.fields || {});
      setMsg(friendlyMessage(err, "Couldn't save. Try again."));
    } finally {
      setBusy("");
    }
  };
  const runTest = async () => {
    setBusy("test");
    setTest(null);
    try {
      const { data } = await http.post("/ai/test", {}, { timeout: 30000 });
      setTest(data);
      const fresh = await http.get("/ai/config");
      setCfg(fresh.data);
    } catch (err) {
      setTest({ ok: false, message: friendlyMessage(err, "Couldn't run the test. Try again.") });
    } finally {
      setBusy("");
    }
  };
  const setMode = (mode) => setField("mode", mode);
  const setField = async (k, v) => {
    const { data } = await http.put("/ai/config", { [k]: v });
    setCfg(data);
  };

  if (!cfg) return <Section title="Our model" testId="settings-our-model"><p className="text-sm text-[var(--dp-ink-3)]">{msg || "Loading..."}</p></Section>;
  return (
    <Section title="Our model" note="Your own model at an OpenAI-compatible address. If it's blank or takes over 20 seconds, the built-in key reads the request. If that fails too, the no-AI reader does." testId="settings-our-model">
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input id="our-model-base-url" label="Base address" value={form.base_url} onChange={(v) => set("base_url", v)} placeholder="https://my-model.example.com" error={errors.base_url} />
          <Input id="our-model-name" label="Model name" value={form.model} onChange={(v) => set("model", v)} placeholder="qwen3-8b-drivepast" />
        </div>
        <button type="button" onClick={() => setForm((f) => ({ ...f, base_url: OPENAI_URL, model: /^(gpt|o\d)/i.test(f.model) ? f.model : "gpt-5-nano" }))}
          className="text-sm font-semibold text-[var(--dp-accent)] underline-offset-4 hover:underline" data-testid="our-model-use-openai-button">
          Use OpenAI (your key): fills the address and gpt-5-nano. Paste your OpenAI key below, then Save.
        </button>
        <div>
          <Input id="our-model-secret" label="Shared secret or API key (optional)" type="password" value={form.secret} onChange={(v) => set("secret", v)} placeholder={cfg.secret_set ? "Saved. Type a new one to replace it" : "Sent as Authorization: Bearer"} />
          {cfg.secret_set && (
            <p className="mt-1 flex items-center gap-3 text-xs text-[var(--dp-ink-3)]">
              <span data-testid="our-model-secret-masked">A key is saved (hidden)</span>
              <button onClick={() => save({ clear_secret: true })} className="font-semibold underline" data-testid="our-model-clear-secret-button">Remove it</button>
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={() => save()} disabled={Boolean(busy)} className="h-10 rounded-full px-5 font-semibold" data-testid="our-model-save-button">{busy === "save" ? "Saving..." : "Save our model"}</Button>
          <Button onClick={runTest} disabled={Boolean(busy)} variant="outline" className="h-10 rounded-full px-5 font-semibold" data-testid="our-model-test-button"><Plug className="mr-2 h-4 w-4" />{busy === "test" ? "Testing (up to 20 s)..." : "Test connection"}</Button>
          {msg && <span className="text-sm text-[var(--dp-ink-2)]" data-testid="our-model-save-status">{msg}</span>}
        </div>
        {test && (
          <p className={`tnum text-sm font-medium ${test.ok ? "text-[var(--dp-green)]" : "text-[var(--dp-amber)]"}`} data-testid="our-model-test-result">
            {test.message}{test.ok && test.model ? ` · ${test.model}` : ""}
          </p>
        )}
        <div>
          <label className="text-sm font-medium" htmlFor="ai-mode">AI mode</label>
          <div className="mt-1.5 flex gap-1 rounded-full bg-[var(--dp-bg)] p-1 sm:w-fit" role="radiogroup" id="ai-mode">
            {Object.entries(cfg.modes).map(([k, label]) => (
              <button key={k} role="radio" aria-checked={cfg.mode === k} onClick={() => setMode(k)} data-testid={`ai-mode-${k}`}
                className={`flex-1 whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${cfg.mode === k ? "bg-[var(--dp-ink)] text-[var(--dp-page)]" : "text-[var(--dp-ink-2)]"}`}>
                {label}
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Pick id="reading-model" label="Reading model" value={cfg.reading_model} options={cfg.models} onChange={(v) => setField("reading_model", v)} />
          <Pick id="reading-examples" label="Examples in the prompt" value={String(cfg.reading_examples)} options={{ 0: "0", 5: "5" }} onChange={(v) => setField("reading_examples", Number(v))} />
          <Pick id="assistant-model" label="Assistant model" value={cfg.assistant_model} options={cfg.models} onChange={(v) => setField("assistant_model", v)} />
        </div>
        <LastAnswered a={cfg.last_answered} />
      </div>
    </Section>
  );
}
