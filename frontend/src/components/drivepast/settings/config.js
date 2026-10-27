export const NUMBER_SECTIONS = [
  {
    title: "Costs and pricing",
    note: "Used to work out what each stop really costs you.",
    fields: [
      { key: "wage_per_hour", label: "Driver wage", prefix: "$", suffix: "per hour", money: true },
      { key: "cost_per_mile", label: "Vehicle cost", prefix: "$", suffix: "per mile", money: true },
      { key: "markup_pct", label: "Markup over added cost", suffix: "%" },
      { key: "floor_recurring", label: "Floor per recurring visit", prefix: "$", money: true },
      { key: "floor_one_off", label: "Floor per one-off run", prefix: "$", money: true },
      { key: "usual_recurring", label: "Usual price per recurring visit", prefix: "$", money: true },
      { key: "usual_one_off", label: "Usual price per one-off run", prefix: "$", money: true },
      { key: "market_ref_low", label: "Market reference, low", prefix: "$", suffix: "per run", money: true },
      { key: "market_ref_high", label: "Market reference, high", prefix: "$", suffix: "per run", money: true },
      { key: "weekdays_per_month", label: "Weekdays per month", suffix: "days" },
    ],
  },
  {
    title: "Travel",
    note: "Changing these re-times every van's route.",
    fields: [
      { key: "speed_sf_mph", label: "San Francisco", suffix: "mph" },
      { key: "speed_eastbay_mph", label: "East Bay", suffix: "mph" },
      { key: "speed_cross_mph", label: "Between SF and the East Bay", suffix: "mph" },
      { key: "bridge_minutes", label: "Bay Bridge extra", suffix: "min" },
      { key: "road_factor", label: "Road factor", hint: "Straight-line miles times this number." },
    ],
  },
  {
    title: "New stops",
    note: "How long a stop from a new request takes.",
    fields: [{ key: "minutes_per_new_stop", label: "Minutes per new stop", suffix: "min" }],
  },
];

export const NUMBER_KEYS = NUMBER_SECTIONS.flatMap((s) => s.fields);

const POSITIVE = new Set(["weekdays_per_month", "speed_sf_mph", "speed_eastbay_mph", "speed_cross_mph", "road_factor", "minutes_per_new_stop"]);
const MAXES = { weekdays_per_month: 31, road_factor: 3, markup_pct: 1000, speed_sf_mph: 80, speed_eastbay_mph: 80, speed_cross_mph: 80, bridge_minutes: 120, minutes_per_new_stop: 120 };

export function checkNumber(key, raw) {
  const text = String(raw ?? "").trim();
  if (text === "" || !/^-?\d*\.?\d+$/.test(text)) return "Enter a number.";
  const n = Number(text);
  if (!Number.isFinite(n)) return "Enter a number.";
  if (n < 0) return "Use 0 or more.";
  if (POSITIVE.has(key) && n <= 0) return "Use a number above 0.";
  if (MAXES[key] !== undefined && n > MAXES[key]) return `Use ${MAXES[key]} or less.`;
  return "";
}

export function displayNumber(field, value) {
  if (typeof value !== "number") return "";
  return field.money ? value.toFixed(2) : String(value);
}

export function checkPhone(raw) {
  const text = raw.trim();
  const digits = text.replace(/\D/g, "");
  if (!text) return "Type a phone number first.";
  if (/[^0-9+()\-. ]/.test(text) || digits.length < 7 || digits.length > 15) return "Use 7 to 15 digits, like (510) 555-0199.";
  return "";
}

export const CLOCK_OPTIONS = Array.from({ length: 57 }, (_, i) => 360 + i * 15);
