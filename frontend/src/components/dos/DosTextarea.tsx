import type { TextareaHTMLAttributes } from 'react';
import styles from './DosTextarea.module.css';

export function DosTextarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={[styles.textarea, className].filter(Boolean).join(' ')} {...props} />;
}
