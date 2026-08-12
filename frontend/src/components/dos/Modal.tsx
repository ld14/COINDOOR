import type { ReactNode } from 'react';
import { useRef } from 'react';
import { useModalFoco } from '@/hooks/useModalFoco';
import styles from './Modal.module.css';

interface ModalProps {
  children?: ReactNode;
  onClose: () => void;
  open?: boolean;
  size?: 'small' | 'medium' | 'large';
  title: string;
}

export function Modal({ children, onClose, open = false, size = 'medium', title }: ModalProps) {
  const ref = useRef<HTMLDivElement>(null);
  useModalFoco(ref, open, onClose);

  if (!open) return null;

  return (
    <div className={styles.backdrop} role="presentation">
      <div aria-modal="true" className={[styles.window, styles[size]].filter(Boolean).join(' ')} ref={ref} role="dialog">
        <div className={styles.titlebar}>
          <span>{title}</span>
          <button aria-label="Cerrar" className={styles.close} onClick={onClose} type="button">X</button>
        </div>
        <div className={styles.body}>{children}</div>
      </div>
    </div>
  );
}
