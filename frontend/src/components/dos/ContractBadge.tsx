import { contractStatus, type ContractStatus } from '@/lib/contractStatus';
import styles from './ContractBadge.module.css';

interface ContractBadgeProps {
  status?: ContractStatus;
  className?: string;
}

/** Indicador chico del contrato: "Contrato ATTRACT v1 ✓" (o ✕ si hay un problema). */
export function ContractBadge({ status = contractStatus, className }: ContractBadgeProps) {
  const classes = [styles.badge, status.ok ? styles.ok : styles.bad, className].filter(Boolean).join(' ');
  return <span className={classes} data-testid="contract-badge">{status.label} <span aria-label={status.ok ? 'válido' : 'con problemas'}>{status.ok ? '✓' : '✕'}</span></span>;
}
