import type { ContractStatus } from '@/lib/contractStatus';
import { ContractBadge } from './ContractBadge';
import styles from './StatusBar.module.css';

const entries = [
  ['F1', 'Ayuda'],
  ['F2', 'Sistemas'],
  ['F3', 'Juegos'],
  ['F4', 'Exportar'],
  ['F5', 'Config'],
  ['/', 'Buscar'],
  ['Esc', 'Cerrar'],
];

interface StatusBarProps {
  contract?: ContractStatus;
}

export function StatusBar({ contract }: StatusBarProps) {
  return (
    <footer className={styles.bar}>
      <div className={styles.keys}>
        {entries.map(([key, label]) => <span key={key}><kbd className={styles.key}>{key}</kbd> {label}</span>)}
      </div>
      <ContractBadge status={contract} />
    </footer>
  );
}
