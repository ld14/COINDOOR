import type { HTMLAttributes, ReactNode } from 'react';
import styles from './SectionHeader.module.css';

interface SectionHeaderProps extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
}

export function SectionHeader({ children, className, ...props }: SectionHeaderProps) {
  return <div className={[styles.header, className].filter(Boolean).join(' ')} {...props}>{children}</div>;
}
