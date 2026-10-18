import { useEffect, useRef, type RefObject } from 'react';

export function useDialogFocus(panel: RefObject<HTMLElement | null>, active: boolean, onClose: () => void) {
  const close = useRef(onClose);
  useEffect(() => { close.current = onClose; }, [onClose]);
  useEffect(() => {
    if (!active || !panel.current) return;
    const element = panel.current;
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    // Keep DOM order and exclude disabled/inert controls, including during saves.
    const focusable = () => [...element.querySelectorAll<HTMLElement>('*')].filter(item =>
      item.tabIndex >= 0 && !item.hasAttribute('disabled') && !item.closest('[hidden], [inert]'));
    (element.querySelector<HTMLElement>('input:not(:disabled), textarea:not(:disabled)') ?? focusable()[0])?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.stopPropagation(); close.current(); }
      if (event.key === 'Tab') {
        const items = focusable(), first = items[0], last = items.at(-1);
        if (!first) event.preventDefault();
        else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    };
    element.addEventListener('keydown', keydown);
    return () => { element.removeEventListener('keydown', keydown); document.body.style.overflow = overflow; previous?.focus(); };
  }, [panel, active]);
}
