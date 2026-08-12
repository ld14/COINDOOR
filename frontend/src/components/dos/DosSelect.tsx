import type { SelectHTMLAttributes } from 'react';
import styles from './DosSelect.module.css';

export function DosSelect({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={[styles.select, className].filter(Boolean).join(' ')} {...props}>{children}</select>;
}
