import type { MouseEvent, ReactNode } from 'react';
import { useId, useRef } from 'react';
import { useModalFoco } from '@/hooks/useModalFoco';
import { Card } from './Card';
import styles from './Modal.module.css';

interface ModalProps {
  /** Color de la banda del encabezado (valor CSS, ej. `var(--accent-3)`). */
  band?: string;
  children?: ReactNode;
  onClose: () => void;
  open?: boolean;
  size?: 'small' | 'medium' | 'large';
  title: string;
}

export function Modal({ band = 'var(--accent)', children, onClose, open = false, size = 'medium', title }: ModalProps) {
  const ref = useRef<HTMLDivElement>(null);
  const pressedBackdrop = useRef(false);
  const titleId = useId();
  useModalFoco(ref, open, onClose);

  if (!open) return null;

  // Cierra solo si el gesto entero (apretar y soltar) fue sobre el fondo: arrastrar una selección hasta afuera no cierra.
  function onBackdropDown(event: MouseEvent<HTMLDivElement>) {
    pressedBackdrop.current = event.target === event.currentTarget;
  }

  function onBackdropClick(event: MouseEvent<HTMLDivElement>) {
    if (pressedBackdrop.current && event.target === event.currentTarget) onClose();
    pressedBackdrop.current = false;
  }

  const close = <button aria-label="Cerrar" className={styles.close} onClick={onClose} type="button">✕</button>;

  return (
    <div className={styles.backdrop} onClick={onBackdropClick} onMouseDown={onBackdropDown} role="presentation">
      <div aria-labelledby={titleId} aria-modal="true" className={[styles.window, styles[size]].join(' ')} ref={ref} role="dialog">
        <Card actions={close} band={band} className={styles.card} title={title} titleId={titleId}>
          {children}
        </Card>
      </div>
    </div>
  );
}
