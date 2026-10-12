import { Card, DosButton } from '@/components/dos';
import type { GuiaChecklistItem } from '@/lib/domain/types';
import { irAPendiente } from './navegacion';
import styles from './ComoSeJuegaSection.module.css';

/** Filas del checklist que se resuelven escribiendo en un campo de «Cómo se juega». */
const CAMPOS_DE_TEXTO = new Set(['objetivo', 'primerosPasos', 'reglasEsenciales']);

interface GuiaChecklistProps {
  items: GuiaChecklistItem[];
  fallos: Record<string, string>;
}

function irACampo(campo: string, etiquetas: string[]) {
  irAPendiente(document, { id: `ir:${campo}`, label: campo, severity: 'required', seccion: 'guia', campo, etiquetas }, true);
}

/** Estado de la guía (solo lectura, columna lateral). Los campos se editan en la sección «Cómo se juega». */
export function GuiaChecklist({ items, fallos }: GuiaChecklistProps) {
  if (items.length === 0) return null;
  const listos = items.filter((item) => item.estado === 'ok').length;
  const sinObjetivo = items.some((item) => item.requerido && item.estado === 'falta');
  return (
    <Card band="var(--accent-2)" hint={`${listos} de ${items.length} listos`} title="Guía: checklist">
      {sinObjetivo ? <p className={`${styles.resumen} ${styles.resumenError}`}>✕ Sin objetivo la guía no se exporta.</p> : null}
      <ul aria-label="Checklist de la guía" className={styles.lista}>
        {items.map((item) => {
          const falla = item.estado === 'falta' ? fallos[item.key] : undefined;
          const ok = item.estado === 'ok';
          const marca = ok ? '✓' : item.requerido ? '✕' : '!';
          const clase = ok ? styles.marcaOk : item.requerido ? styles.marcaError : styles.marcaRevisar;
          const nombreMarca = ok ? 'Listo' : item.requerido ? 'Falta (obligatorio)' : 'Revisar';
          const detalle = falla ? `No se pudo generar: ${falla}. ${item.detalle}` : item.detalle;
          return (
            <li className={styles.fila} data-estado={item.estado} data-requerido={item.requerido} key={item.key}>
              <span aria-label={nombreMarca} className={`${styles.marca} ${clase}`} role="img">{marca}</span>
              <span className={styles.nombre}>
                <span className={styles.etiqueta}>{item.label}</span>
                <span className={`${styles.detalle} ${falla ? styles.detalleError : ''}`}>{detalle}</span>
              </span>
              <span className={styles.accion}>
                {!ok && CAMPOS_DE_TEXTO.has(item.key) ? (
                  <DosButton aria-label={`Escribir ${item.label.toLowerCase()}`} onClick={() => irACampo(item.key, [item.label])} size="sm" variant="secondary">Escribir ↑</DosButton>
                ) : null}
                {!ok && item.key === 'jugadores' ? (
                  <DosButton aria-label="Ir a Jugadores en Identidad" onClick={() => irACampo('players', ['Jugadores'])} size="sm" variant="secondary">Ir a Identidad ↑</DosButton>
                ) : null}
              </span>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
