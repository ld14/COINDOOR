import styles from './ProgressBar.module.css';

interface ProgressBarProps {
  value?: number;
}

export function ProgressBar({ value = 0 }: ProgressBarProps) {
  const safeValue = Math.max(0, Math.min(100, value));
  return <progress aria-label="Progreso" className={styles.progress} max={100} value={safeValue} />;
}
