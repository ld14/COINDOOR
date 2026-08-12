import type { InputHTMLAttributes } from 'react';
import styles from './DosInput.module.css';

export function DosInput({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={[styles.input, className].filter(Boolean).join(' ')} {...props} />;
}
