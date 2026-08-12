import type { ButtonHTMLAttributes, ReactNode } from 'react';
import styles from './DosButton.module.css';

export type DosButtonVariant = 'primary' | 'primary-small' | 'ghost' | 'ghost-small' | 'danger-small';

const variantClass: Record<DosButtonVariant, string> = {
  primary: styles.primary,
  'primary-small': styles.primarySmall,
  ghost: styles.ghost,
  'ghost-small': styles.ghostSmall,
  'danger-small': styles.dangerSmall,
};

interface DosButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children?: ReactNode;
  pressed?: boolean;
  variant?: DosButtonVariant;
}

export function DosButton({ children, className, pressed = false, type = 'button', variant = 'ghost', ...props }: DosButtonProps) {
  const classes = [styles.button, variantClass[variant], pressed ? styles.pressed : '', className].filter(Boolean).join(' ');
  return <button className={classes} type={type} {...props}>{children}</button>;
}
