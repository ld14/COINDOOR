import type { SelectHTMLAttributes } from 'react';
import { useId } from 'react';
import styles from './DosSelect.module.css';

interface DosSelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  /** Mensaje de error debajo del campo; implica `invalid`. */
  errorMessage?: string;
  invalid?: boolean;
}

export function DosSelect({ className, children, errorMessage, invalid = false, 'aria-describedby': describedBy, ...props }: DosSelectProps) {
  const errorId = useId();
  const isInvalid = invalid || !!errorMessage;
  const described = [describedBy, errorMessage ? errorId : ''].filter(Boolean).join(' ') || undefined;
  const select = (
    <select
      aria-describedby={described}
      aria-invalid={isInvalid || undefined}
      className={[styles.select, isInvalid ? styles.invalid : '', className].filter(Boolean).join(' ')}
      {...props}
    >
      {children}
    </select>
  );
  if (!errorMessage) return select;
  return <>{select}<span className={styles.error} id={errorId}>{errorMessage}</span></>;
}
