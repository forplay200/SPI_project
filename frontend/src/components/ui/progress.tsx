export function Progress({ value, label }: { value: number; label?: string }) {
  const safe = Math.min(100, Math.max(0, value));
  return (
    <div>
      <div
        className="h-2 overflow-hidden rounded-full bg-subtle"
        role="progressbar"
        aria-label={label ?? "Progress"}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={safe}
      >
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${safe}%` }}
        />
      </div>
      {label ? <p className="mt-2 text-sm text-ink-muted">{label}</p> : null}
    </div>
  );
}
