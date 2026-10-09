import styles from './StatusBadge.module.css';

export type GameStatus = 'ready' | 'incomplete' | 'error' | 'exported';

const label: Record<GameStatus, string> = {
  incomplete: '● En carga',
  ready: '✓ Listo',
  error: '✕ Con errores',
  exported: '⇪ Exportado',
};

interface StatusBadgeProps {
  status?: GameStatus;
}

/** Estado del juego. Siempre lleva ícono y texto: el color nunca es el único portador. */
export function StatusBadge({ status = 'incomplete' }: StatusBadgeProps) {
  return <span className={[styles.badge, styles[status]].join(' ')}>{label[status]}</span>;
}
