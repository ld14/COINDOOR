import { useSaveStatus } from '@/hooks/useSaveStatus';
import { useFichaAutosave } from './autosaveContext';
import styles from './EstadoGuardado.module.css';

/**
 * Si lo editado ya quedó en la ficha, al lado de lo que se edita: el indicador de la barra superior
 * queda lejos de una lista larga. No es un botón: el guardado de la ficha es el autosave (feature 019).
 */
export function EstadoGuardado() {
  const { pendiente } = useFichaAutosave();
  const status = useSaveStatus();

  if (status.kind === 'error' && !pendiente) {
    return <p className={styles.error}>No se pudo guardar: reintentá desde la barra superior.</p>;
  }
  const texto = pendiente ? 'Cambios sin guardar' : status.kind === 'saving' ? 'Guardando…' : 'Todo guardado';
  return <p className={styles.estado}>Se guarda solo · {texto}</p>;
}
