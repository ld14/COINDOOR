import type { TextareaHTMLAttributes } from 'react';
import { useId } from 'react';
import styles from './DosTextarea.module.css';

interface DosTextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Mensaje de error debajo del campo; implica `invalid`. */
  errorMessage?: string;
  invalid?: boolean;
}

export function DosTextarea({ className, errorMessage, invalid = false, 'aria-describedby': describedBy, ...props }: DosTextareaProps) {
  const errorId = useId();
  const isInvalid = invalid || !!errorMessage;
  const described = [describedBy, errorMessage ? errorId : ''].filter(Boolean).join(' ') || undefined;
  const textarea = (
    <textarea
      aria-describedby={described}
      aria-invalid={isInvalid || undefined}
      className={[styles.textarea, isInvalid ? styles.invalid : '', className].filter(Boolean).join(' ')}
      {...props}
    />
  );
  if (!errorMessage) return textarea;
  return <>{textarea}<span className={styles.error} id={errorId}>{errorMessage}</span></>;
}
