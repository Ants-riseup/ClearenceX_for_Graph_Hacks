import { useEffect, useId, useRef, type ReactNode } from 'react';
import { useDialogFocus } from '../../hooks/useDialogFocus';

/** Keeps keyboard focus inside an open confirmation and restores it on close. */
export function Modal({ title, description, children, busy = false, onClose }: {
  title: string; description: string; children: ReactNode; busy?: boolean; onClose: () => void;
}) {
  const id = useId();
  const panel = useRef<HTMLDivElement>(null);
  useDialogFocus(panel, true, () => { if (!busy) onClose(); });
  useEffect(() => {
    const active = document.activeElement;
    if (panel.current && (!panel.current.contains(active) || active?.hasAttribute('disabled'))) {
      (panel.current.querySelector<HTMLElement>('input:not(:disabled)') ?? panel.current).focus();
    }
  }, [busy]);
  return <div className="fixed inset-0 z-[100] bg-[#0d1b3e]/60 backdrop-blur-sm grid place-items-center p-4" onMouseDown={event => { if (event.target === event.currentTarget && !busy) onClose(); }}>
    <div ref={panel} tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby={`${id}-title`} aria-describedby={`${id}-description`} className="w-full max-w-lg max-h-[90dvh] overflow-y-auto rounded-2xl bg-surface-container-lowest p-6 shadow-2xl">
      <h2 id={`${id}-title`} className="text-xl font-bold break-words">{title}</h2><p id={`${id}-description`} className="text-sm text-on-surface-variant mt-2 mb-5">{description}</p>{children}
    </div>
  </div>;
}
