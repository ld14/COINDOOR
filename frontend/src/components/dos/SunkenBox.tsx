import type { HTMLAttributes, ReactNode } from 'react';
import styles from './SunkenBox.module.css';

interface SunkenBoxProps extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
}

export function SunkenBox({ children, className, ...props }: SunkenBoxProps) {
  return <div className={[styles.box, className].filter(Boolean).join(' ')} {...props}>{children}</div>;
}
