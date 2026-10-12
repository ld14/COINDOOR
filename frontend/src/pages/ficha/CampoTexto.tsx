import type { ReactNode } from 'react';
import { DosButton, OriginChip } from '@/components/dos';
import type { Game, TextKey } from '@/lib/domain/types';
import { useFichaAutosave } from './autosaveContext';
import { confirmManualDelete } from './helpers';
import styles from './TextosSection.module.css';

export interface CampoProps {
  campo: TextKey;
  etiqueta: string;
  game: Game;
  /** Obligatorio que bloquea algo: vacío se pinta en error con este motivo. */
  bloqueo?: string;
  acciones?: ReactNode;
  ayuda?: string;
  contador?: { actual: number; maximo?: number };
  children: ReactNode;
  onDelete: (key: string) => void;
}

/** Un campo de texto de la ficha: rótulo, origen, contador, acciones, aceptar/borrar. Lo usan Textos y Cómo se juega. */
export function Campo({ campo, etiqueta, game, bloqueo, acciones, ayuda, contador, children, onDelete }: CampoProps) {
  const { aceptar } = useFichaAutosave();
  const field = game.texts[campo];
  const status = field?.status ?? 'empty';
  const bloquea = status === 'empty' && !!bloqueo;
  return (
    <div className={[styles.campo, status === 'suggested' ? styles.sugerido : ''].filter(Boolean).join(' ')} data-bloquea={bloquea || undefined} data-estado={status} data-grupo={campo}>
      <div className={styles.cabecera}>
        <span className={styles.rotulo}>{etiqueta}</span>
        <OriginChip required={bloquea} source={field?.source} status={status} />
        {contador ? (
          <span className={[styles.contador, contador.maximo && contador.actual >= contador.maximo ? styles.contadorLleno : ''].filter(Boolean).join(' ')}>
            {contador.actual}{contador.maximo ? ` / ${contador.maximo}` : ''}
          </span>
        ) : null}
        <div className={styles.acciones}>
          {acciones}
          {status !== 'empty' ? (
            <DosButton onClick={() => confirmManualDelete(status, () => onDelete(campo))} size="sm" title="Borrar" variant="ghost">Borrar</DosButton>
          ) : null}
        </div>
      </div>
      {children}
      {bloquea ? <p className={styles.error}>✕ {bloqueo}</p> : null}
      {ayuda ? <p className={styles.ayuda}>{ayuda}</p> : null}
      {status === 'suggested' ? (
        <div className={styles.pie}>
          <DosButton aria-label={`Aceptar ${etiqueta.toLowerCase()}`} onClick={() => aceptar(campo)} size="sm" variant="primary">✓ Aceptar</DosButton>
          <span className={styles.atajo}>Aceptar como está, o editalo y queda como Manual.</span>
        </div>
      ) : null}
    </div>
  );
}
