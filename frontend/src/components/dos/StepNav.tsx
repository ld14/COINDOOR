import type { ReactNode } from 'react';
import styles from './StepNav.module.css';

/** current = en curso, complete = completa, blocking = bloquea la exportación, review = algo para revisar. */
export type StepStatus = 'current' | 'complete' | 'blocking' | 'review';

export interface StepNavItem {
  id: string;
  label: ReactNode;
  status?: StepStatus;
  /** Texto corto del pendiente: "Objetivo obligatorio", "5 sugeridos". */
  hint?: string;
}

interface StepNavProps {
  items: StepNavItem[];
  /** Sección visible actualmente (aria-current="step"). */
  activeId?: string;
  /** Recibe el id de la sección; quien lo usa hace el scroll. */
  onSelect?: (id: string) => void;
  'aria-label'?: string;
  className?: string;
}

const statusClass: Record<StepStatus, string> = {
  current: styles.current,
  complete: styles.complete,
  blocking: styles.blocking,
  review: styles.review,
};

const statusText: Record<StepStatus, string> = {
  current: 'en curso',
  complete: 'completa',
  blocking: 'bloquea la exportación',
  review: 'para revisar',
};

function marker(status: StepStatus, index: number): string {
  if (status === 'complete') return '✓';
  if (status === 'blocking') return '!';
  return String(index + 1);
}

export function StepNav({ items, activeId, onSelect, className, 'aria-label': ariaLabel = 'Secciones de la ficha' }: StepNavProps) {
  return (
    <nav aria-label={ariaLabel} className={[styles.nav, className].filter(Boolean).join(' ')}>
      <ol className={styles.list}>
        {items.map((item, index) => {
          const status = item.status ?? 'current';
          const active = item.id === activeId;
          return (
            <li key={item.id}>
              <button
                aria-current={active ? 'step' : undefined}
                className={[styles.step, statusClass[status], active ? styles.active : ''].filter(Boolean).join(' ')}
                data-status={status}
                onClick={() => onSelect?.(item.id)}
                type="button"
              >
                <span aria-hidden="true" className={styles.marker}>{marker(status, index)}</span>
                <span className={styles.label}>{item.label}</span>
                {item.hint ? <span className={styles.hint}>{item.hint}</span> : null}
                <span className={styles.srOnly}>{`, ${statusText[status]}`}</span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
