const moneyFmt = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function money(n) {
  if (typeof n !== "number" || !Number.isFinite(n)) return "--";
  return `$${moneyFmt.format(n)}`;
}

export function pct(n) {
  if (typeof n !== "number" || !Number.isFinite(n)) return "--";
  return `${n.toFixed(1)}%`;
}

export function fmtTime(minutes) {
  if (typeof minutes !== "number" || !Number.isFinite(minutes)) return "";
  const total = ((Math.round(minutes) % 1440) + 1440) % 1440;
  const h = Math.floor(total / 60);
  const m = total % 60;
  return `${h % 12 || 12}:${String(m).padStart(2, "0")}${h < 12 ? "am" : "pm"}`;
}

export function plural(n, one, many) {
  return `${n} ${n === 1 ? one : many}`;
}
