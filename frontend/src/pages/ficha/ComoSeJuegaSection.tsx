import { Panel, SectionHeader, SunkenBox } from '@/components/dos';
import type { GuiaChecklistItem } from '@/lib/domain/types';
import styles from '../ReadPages.module.css';

export function GuiaChecklist({ items, fallos }: { items: GuiaChecklistItem[]; fallos: Record<string, string> }) {
  if (items.length === 0) return null;
  const listos = items.filter((item) => item.estado === 'ok').length;
  const sinObjetivo = items.some((item) => item.requerido && item.estado === 'falta');
  return (
    <Panel>
      <SectionHeader>CÓMO SE JUEGA — CHECKLIST</SectionHeader>
      <SunkenBox>
        <p className={styles.meta}>
          {listos} de {items.length} listos.{sinObjetivo ? ' Sin objetivo la guía no se exporta.' : ''}
        </p>
        <ul aria-label="Checklist de la guía" className={styles.checklist}>
          {items.map((item) => {
            const falla = item.estado === 'falta' ? fallos[item.key] : undefined;
            const marca = item.estado === 'ok' ? '✓' : item.requerido ? '✗' : '○';
            return (
              <li className={styles.completionTile} data-estado={item.estado} key={item.key}>
                <span aria-hidden className={styles.tileMark}>{marca}</span>
                <span className={styles.name}>{item.label}</span>
                <span className={styles.meta}>
                  {item.estado === 'ok' ? 'Listo' : item.requerido ? 'Falta (obligatorio)' : 'Falta'}
                  {' — '}
                  {falla ? `No se pudo generar: ${falla}. ${item.detalle}` : item.detalle}
                </span>
              </li>
            );
          })}
        </ul>
      </SunkenBox>
    </Panel>
  );
}
