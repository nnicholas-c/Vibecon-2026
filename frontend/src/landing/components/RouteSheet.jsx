export function Row({ label, value, strong, testid }) {
  return (
    <div className={`lp-row ${strong ? "lp-row-strong" : ""}`} data-testid={testid}>
      <span>{label}</span>
      <span className={strong ? "font-semibold" : ""} data-testid={testid ? `${testid}-value` : undefined}>
        {value}
      </span>
    </div>
  );
}

export default function RouteSheet({ n, name, tag, title, side = "left", children, testid }) {
  return (
    <div className={`lp-sheet ${side === "right" ? "lp-sheet-right" : ""}`} data-testid={testid}>
      <div className="lp-sheet-head">
        <span className="lp-sheet-num">{n}</span>
        <span className="flex-1 px-3">{name}</span>
        <span className="pr-3 text-[#5C5A54]">{tag}</span>
      </div>
      <div className="lp-sheet-body">
        <h2 className="lp-h2">{title}</h2>
        {children}
      </div>
    </div>
  );
}
