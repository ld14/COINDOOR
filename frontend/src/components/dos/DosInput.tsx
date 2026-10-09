import type { InputHTMLAttributes } from 'react';
import { useId } from 'react';
import styles from './DosInput.module.css';

interface DosInputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Mensaje de error debajo del campo; implica `invalid`. */
  errorMessage?: string;
  invalid?: boolean;
}

export function DosInput({ className, errorMessage, invalid = false, 'aria-describedby': describedBy, ...props }: DosInputProps) {
  const errorId = useId();
  const isInvalid = invalid || !!errorMessage;
  const described = [describedBy, errorMessage ? errorId : ''].filter(Boolean).join(' ') || undefined;
  const input = (
    <input
      aria-describedby={described}
      aria-invalid={isInvalid || undefined}
      className={[styles.input, isInvalid ? styles.invalid : '', className].filter(Boolean).join(' ')}
      {...props}
    />
  );
  if (!errorMessage) return input;
  return <>{input}<span className={styles.error} id={errorId}>{errorMessage}</span></>;
}
