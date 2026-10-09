import { useEffect, useId, useMemo } from 'react';
import styles from './NextPendingCard.module.css';

export interface PendingItem {
  id: string;
  label: string;
  /** required = obligatorio (bloquea exportar, rojo); review = para revisar (ámbar). */
  severity: 'required' | 'review';
  /** Número de la sección a la que lleva ("Ir → 3"). */
  step?: number;
}

interface NextPendingCardProps {
  items: PendingItem[];
  onGo: (item: PendingItem) => void;
  /** Tecla de atajo global (se muestra como <kbd>). null desactiva el atajo. */
  shortcut?: string | null;
  className?: string;
}

function isEditable(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) || target.closest('[role="dialog"]') !== null;
}

/** Obligatorios primero, revisiones después; dentro de cada grupo se respeta el orden recibido. */
function sortPending(items: PendingItem[]): PendingItem[] {
  return [...items.filter((i) => i.severity === 'required'), ...items.filter((i) => i.severity !== 'required')];
}

export function NextPendingCard({ items, onGo, shortcut = 'N', className }: NextPendingCardProps) {
  const queue = useMemo(() => sortPending(items), [items]);
  const next = queue[0];
  const rest = queue.slice(1);
  const titleId = useId();

  useEffect(() => {
    if (!shortcut || !next) return undefined;
    function onKeyDown(event: KeyboardEvent) {
      if (event.ctrlKey || event.metaKey || event.altKey || isEditable(event.target)) return;
      if (event.key.toLowerCase() !== shortcut!.toLowerCase()) return;
      event.preventDefault();
      onGo(next);
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [shortcut, next, onGo]);

  return (
    <section aria-labelledby={titleId} className={[styles.card, className].filter(Boolean).join(' ')}>
      <h3 className={styles.title} id={titleId}>Siguiente pendiente</h3>
      {next ? (
        <>
          <p className={styles.next}>
            <span className={[styles.dot, next.severity === 'required' ? styles.required : styles.review].join(' ')} aria-hidden="true" />
            {next.label}
          </p>
          <button className={styles.go} onClick={() => onGo(next)} type="button">
            {next.step !== undefined ? `Ir → ${next.step}` : 'Ir →'}
            {shortcut ? <kbd className={styles.kbd}>{shortcut}</kbd> : null}
          </button>
          {rest.length > 0 ? (
            <ul aria-label="Cola de pendientes" className={styles.queue}>
              {rest.map((item) => (
                <li className={item.severity === 'required' ? styles.required : styles.review} data-severity={item.severity} key={item.id}>
                  {item.label}
                </li>
              ))}
            </ul>
          ) : null}
        </>
      ) : (
        <p className={styles.next}>Todo al día. No quedan pendientes.</p>
      )}
    </section>
  );
}
