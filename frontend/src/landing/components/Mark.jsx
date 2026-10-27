export function Mark() {
  return (
    <svg width="34" height="24" viewBox="0 0 34 24" aria-hidden="true" className="shrink-0">
      <path
        d="M2 19 H11 C13.5 19 14 11.5 17 11.5 C20 11.5 20.5 19 23 19 H32"
        fill="none"
        stroke="#141414"
        strokeWidth="2.2"
        strokeLinecap="square"
      />
      <circle cx="17" cy="5" r="3.4" fill="#FF5B1F" stroke="#141414" strokeWidth="1.4" />
    </svg>
  );
}

export function Wordmark({ testid = "landing-wordmark" }) {
  return (
    <span className="flex items-center gap-2" data-testid={testid}>
      <Mark />
      <span className="lp-wordmark">Drivepast</span>
    </span>
  );
}
