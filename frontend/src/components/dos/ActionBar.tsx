import type { ReactNode } from 'react';
import styles from './ActionBar.module.css';

export interface ActionBarShortcut {
  keys: string;
  label: string;
}

interface ActionBarProps {
  /** Progreso de completitud, 0–100. */
  percent: number;
  requiredCount?: number;
  reviewCount?: number;
  shortcuts?: ActionBarShortcut[];
  onSaveDraft?: () => void;
  onExport?: () => void;
  /** Si viene, Exportar queda deshabilitado y muestra el motivo: "faltan 3" → "Exportar (faltan 3)". */
  exportDisabledReason?: string;
  saveLabel?: string;
  exportLabel?: string;
  /** Contenido extra antes de los botones. */
  children?: ReactNode;
  className?: string;
}

export function ActionBar({
  percent,
  requiredCount = 0,
  reviewCount = 0,
  shortcuts = [],
  onSaveDraft,
  onExport,
  exportDisabledReason,
  saveLabel = 'Guardar borrador y salir',
  exportLabel = 'Exportar',
  children,
  className,
}: ActionBarProps) {
  const value = Number.isFinite(percent) ? Math.min(100, Math.max(0, Math.round(percent))) : 0;
  const exportBlocked = Boolean(exportDisabledReason);
  const parts = [`${value}%`];
  if (requiredCount > 0) parts.push(`${requiredCount} ${requiredCount === 1 ? 'obligatorio' : 'obligatorios'}`);
  if (reviewCount > 0) parts.push(`${reviewCount} para revisar`);

  return (
    <footer className={[styles.bar, className].filter(Boolean).join(' ')}>
      <div className={styles.progress}>
        <div aria-label="Progreso de la ficha" aria-valuemax={100} aria-valuemin={0} aria-valuenow={value} className={styles.track} role="progressbar">
          <i className={styles.fill} style={{ width: `${value}%` }} />
        </div>
        <span aria-live="polite" className={styles.text} role="status">{parts.join(' · ')}</span>
      </div>
      {shortcuts.length > 0 ? (
        <span className={styles.keys}>
          {shortcuts.map((s) => (
            <span className={styles.key} key={s.keys}><kbd className={styles.kbd}>{s.keys}</kbd>{s.label}</span>
          ))}
        </span>
      ) : null}
      <div className={styles.actions}>
        {children}
        <button className={styles.secondary} onClick={onSaveDraft} type="button">{saveLabel}</button>
        <button
          aria-disabled={exportBlocked || undefined}
          className={[styles.primary, exportBlocked ? styles.blocked : ''].filter(Boolean).join(' ')}
          onClick={() => { if (!exportBlocked) onExport?.(); }}
          title={exportDisabledReason}
          type="button"
        >
          {`⇪ ${exportLabel}`}
          {exportBlocked ? <small className={styles.reason}>{` (${exportDisabledReason})`}</small> : null}
        </button>
      </div>
    </footer>
  );
}
