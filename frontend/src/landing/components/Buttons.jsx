export function PrimaryButton({ children, className = "", ...rest }) {
  return (
    <button type="button" className={`lp-btn lp-btn-primary ${className}`} {...rest}>
      {children}
    </button>
  );
}

export function SecondaryButton({ children, className = "", ...rest }) {
  return (
    <button type="button" className={`lp-btn lp-btn-secondary ${className}`} {...rest}>
      {children}
    </button>
  );
}
