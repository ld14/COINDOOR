import { DosButton } from '@/components/dos';
import styles from './NuevoJuego.module.css';

interface Props {
  archivo: string;
  sistema: string;
  tratamiento: string;
  titulo: string;
  /** null = el sistema no tiene precarga. */
  precargaLabel: string | null;
  precarga: boolean;
  onPrecarga: (valor: boolean) => void;
  creando: boolean;
  onCrear: () => void;
}

export function ResumenAlta({ archivo, sistema, tratamiento, titulo, precargaLabel, precarga, onPrecarga, creando, onCrear }: Props) {
  const fila = (etiqueta: string, valor: string, mono = false) => (
    <div className={styles.sumRow}>
      <dt>{etiqueta}</dt>
      <dd className={mono ? styles.mono : undefined}>{valor || '—'}</dd>
    </div>
  );
  return (
    <aside aria-label="Resumen del alta" className={styles.summary}>
      <h2 className={styles.summaryTitle}>Resumen del alta</h2>
      <dl className={styles.sumList}>
        {fila('Archivo', archivo, true)}
        {fila('Sistema', sistema)}
        {fila('Tratamiento', tratamiento)}
        {fila('Título', titulo)}
      </dl>
      <label className={styles.check}>
        <input checked={precargaLabel !== null && precarga} disabled={precargaLabel === null} onChange={(event) => onPrecarga(event.target.checked)} type="checkbox" />
        <span>{precargaLabel ?? 'Este sistema no tiene precarga'}</span>
      </label>
      <DosButton disabled={creando} onClick={onCrear} variant="primary">
        {creando ? 'Creando…' : 'Crear ficha y empezar a cargar →'}
      </DosButton>
    </aside>
  );
}
