import styles from './ProgressBar.module.css';

export type ProgressState = 'active' | 'ok' | 'error';

interface ProgressBarProps {
  /** Etiqueta accesible. */
  label?: string;
  /** Color del relleno: en curso (accent), completo (ok) o con falla (error). */
  state?: ProgressState;
  value?: number;
}

export function ProgressBar({ label = 'Progreso', state = 'active', value = 0 }: ProgressBarProps) {
  const safeValue = Math.max(0, Math.min(100, Number.isFinite(value) ? value : 0));
  return (
    <div
      aria-label={label}
      aria-valuemax={100}
      aria-valuemin={0}
      aria-valuenow={Math.round(safeValue)}
      className={[styles.track, styles[state]].join(' ')}
      role="progressbar"
    >
      <div className={styles.fill} style={{ width: `${safeValue}%` }} />
    </div>
  );
}
