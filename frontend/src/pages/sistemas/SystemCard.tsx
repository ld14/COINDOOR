import { useNavigate } from 'react-router-dom';
import { Card, DosButton } from '@/components/dos';
import type { System } from '@/lib/domain/types';
import styles from './sistemas.module.css';

/** Texto del ícono: el nombre corto en mayúsculas, máximo 4 caracteres. */
function iconText(system: System): string {
  return (system.shortName || system.name).slice(0, 4).toUpperCase();
}

export function SystemCard({ system }: { system: System }) {
  const navigate = useNavigate();
  return (
    <Card className={styles.scard}>
      <div className={styles.top}>
        <span aria-hidden="true" className={styles.ico}>{iconText(system)}</span>
        <div className={styles.names}>
          <span className={styles.name}>{system.name}</span>
          <code className={styles.short}>{system.shortName}</code>
        </div>
        <span className={styles.count}><b>{system.gameCount}</b> juegos</span>
      </div>
      <div>
        <div className={styles.fieldHead}>
          <span>Comando de lanzamiento</span>
          {system.valid ? <span className={styles.ok}>✓ existe</span> : <span className={styles.invalidTag}>CABECERA INVÁLIDA</span>}
        </div>
        <div className={styles.cmd}>{system.launchCmd}</div>
        {!system.valid ? <p className={styles.bad}>✕ no existe{system.errorMsg ? ` · ${system.errorMsg}` : ''}</p> : null}
      </div>
      <div className={styles.actions}>
        <DosButton onClick={() => navigate(`/juegos?systemId=${encodeURIComponent(system.id)}`)} size="sm" variant="ghost">
          Ver juegos
        </DosButton>
        {/* TODO(backend): no existe PUT/PATCH /api/systems/{id}; hasta que exista, la edición queda deshabilitada. */}
        <DosButton disabled disabledReason="Editar sistemas todavía no está disponible: falta el endpoint en el backend." size="sm" variant="secondary">
          Editar
        </DosButton>
      </div>
    </Card>
  );
}
