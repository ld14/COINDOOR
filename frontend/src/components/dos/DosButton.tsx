import type { ButtonHTMLAttributes, ReactNode } from 'react';
import styles from './DosButton.module.css';

export type DosButtonVariant =
  | 'primary'
  | 'secondary'
  | 'ghost'
  | 'danger'
  | 'primary-small'
  | 'ghost-small'
  | 'danger-small';

export type DosButtonSize = 'md' | 'sm';

const variantClass: Record<DosButtonVariant, string> = {
  primary: styles.primary,
  secondary: styles.secondary,
  ghost: styles.ghost,
  danger: styles.danger,
  'primary-small': styles.primary,
  'ghost-small': styles.ghost,
  'danger-small': styles.danger,
};

/** Las variantes `*-small` son alias históricos: fuerzan size `sm`. */
const smallAlias: ReadonlySet<DosButtonVariant> = new Set<DosButtonVariant>(['primary-small', 'ghost-small', 'danger-small']);

interface DosButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children?: ReactNode;
  /** Motivo por el que está deshabilitado; se muestra como `title`. */
  disabledReason?: string;
  pressed?: boolean;
  size?: DosButtonSize;
  variant?: DosButtonVariant;
}

export function DosButton({
  children,
  className,
  disabled,
  disabledReason,
  pressed = false,
  size = 'md',
  title,
  type = 'button',
  variant = 'ghost',
  ...props
}: DosButtonProps) {
  const small = size === 'sm' || smallAlias.has(variant);
  const classes = [
    styles.button,
    variantClass[variant],
    small ? styles.small : '',
    pressed ? styles.pressed : '',
    className,
  ].filter(Boolean).join(' ');
  const shownTitle = disabled && disabledReason ? disabledReason : title;
  return (
    <button className={classes} disabled={disabled} title={shownTitle} type={type} {...props}>
      {children}
    </button>
  );
}
