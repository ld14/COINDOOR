import type { CSSProperties, HTMLAttributes, ReactNode } from 'react';
import styles from './Card.module.css';

export interface CardProps extends Omit<HTMLAttributes<HTMLDivElement>, 'title'> {
  /** Botones u otros controles alineados a la derecha del encabezado. */
  actions?: ReactNode;
  /** Color de la banda del encabezado, como valor CSS (ej. `var(--accent-3)`). */
  band?: string;
  /** Color del texto sobre la banda. Por defecto se deduce de `band`. */
  bandInk?: string;
  children?: ReactNode;
  hint?: ReactNode;
  /** Número del círculo del encabezado (sección). */
  number?: number;
  /** Si falta, la tarjeta se renderiza sin encabezado (uso como Panel). */
  title?: ReactNode;
  /** `id` del título, para `aria-labelledby` de quien contiene la tarjeta. */
  titleId?: string;
}

/** Sobre una banda `accent-2` (amarilla) el texto va en tinta oscura. */
function defaultInk(band: string): string {
  return band.includes('--accent-2') ? 'var(--ink-on-accent-2)' : 'var(--ink-on-accent)';
}

export function Card({ actions, band = 'var(--accent)', bandInk, children, className, hint, number, title, titleId, style, ...props }: CardProps) {
  const classes = [styles.card, title === undefined ? styles.plain : '', className].filter(Boolean).join(' ');

  if (title === undefined) {
    return <div className={classes} style={style} {...props}>{children}</div>;
  }

  const bandStyle = { '--card-band': band, '--card-band-ink': bandInk ?? defaultInk(band) } as CSSProperties;
  return (
    <div className={classes} style={style} {...props}>
      <header className={styles.head} style={bandStyle}>
        {number !== undefined ? <span aria-hidden="true" className={styles.number}>{number}</span> : null}
        <h2 className={styles.title} id={titleId}>{title}</h2>
        {hint ? <span className={styles.hint}>{hint}</span> : null}
        {actions ? <div className={styles.actions}>{actions}</div> : null}
      </header>
      <div className={styles.body}>{children}</div>
    </div>
  );
}
