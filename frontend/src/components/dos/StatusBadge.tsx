import styles from './StatusBadge.module.css';

export type GameStatus = 'ready' | 'incomplete' | 'error';

const label: Record<GameStatus, string> = {
  ready: 'LISTO',
  incomplete: 'INCOMPLETO',
  error: 'CON ERRORES',
};

interface StatusBadgeProps {
  status?: GameStatus;
}

export function StatusBadge({ status = 'incomplete' }: StatusBadgeProps) {
  return <span className={[styles.badge, styles[status]].join(' ')}>{label[status]}</span>;
}
