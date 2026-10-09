import { useId } from 'react';
import type { ReactNode } from 'react';
import styles from './CheckTile.module.css';

interface CheckTileProps {
  label: ReactNode;
  /** Metadato a la derecha: tamaño en mono, cantidad, etc. */
  meta?: ReactNode;
  checked: boolean;
  onChange?: (checked: boolean) => void;
  disabled?: boolean;
  /** Motivo por el que no se puede tildar ("no hay trucos", "sin cargar"). Reemplaza al metadato. */
  disabledReason?: string;
  className?: string;
}

export function CheckTile({ label, meta, checked, onChange, disabled = false, disabledReason, className }: CheckTileProps) {
  const reasonId = useId();
  const showReason = disabled && Boolean(disabledReason);
  return (
    <label className={[styles.tile, checked ? styles.checked : '', disabled ? styles.disabled : '', className].filter(Boolean).join(' ')}>
      <input
        aria-describedby={showReason ? reasonId : undefined}
        checked={checked}
        className={styles.input}
        disabled={disabled}
        onChange={(event) => { if (!disabled) onChange?.(event.currentTarget.checked); }}
        type="checkbox"
      />
      <span aria-hidden="true" className={styles.box}>{checked ? '✓' : ''}</span>
      <span className={styles.label}>{label}</span>
      {showReason ? <span className={styles.meta} id={reasonId}>{disabledReason}</span> : meta ? <span className={styles.meta}>{meta}</span> : null}
    </label>
  );
}
