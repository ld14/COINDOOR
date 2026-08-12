import type { HTMLAttributes, ReactNode } from 'react';
import styles from './Panel.module.css';

interface PanelProps extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
}

export function Panel({ children, className, ...props }: PanelProps) {
  return <div className={[styles.panel, className].filter(Boolean).join(' ')} {...props}>{children}</div>;
}
