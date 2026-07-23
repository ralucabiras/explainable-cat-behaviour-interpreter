import { useEffect, useRef } from "react";

export function ConfirmDialog({
  title,
  children,
  confirmLabel,
  busy = false,
  onConfirm,
  onCancel,
}: {
  title: string;
  children: React.ReactNode;
  confirmLabel: string;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const dialogRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busy) onCancel();
    };
    document.addEventListener("keydown", closeOnEscape);
    dialogRef.current?.querySelector<HTMLElement>("[autofocus]")?.focus();
    return () => {
      document.removeEventListener("keydown", closeOnEscape);
      previous?.focus();
    };
  }, [busy, onCancel]);
  return <div className="dialog-backdrop" role="presentation">
    <div ref={dialogRef} className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
      <p className="eyebrow">Permanent action</p>
      <h2 id="confirm-title">{title}</h2>
      <div>{children}</div>
      <div className="dialog-actions">
        <button className="quiet" onClick={onCancel} disabled={busy} autoFocus>Cancel</button>
        <button className="danger-button" onClick={onConfirm} disabled={busy}>
          {busy ? "Deleting…" : confirmLabel}
        </button>
      </div>
    </div>
  </div>;
}
