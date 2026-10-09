import { DosButton } from '@/components/dos';
import { esFuenteIA } from './fuenteIA';
import styles from './origenIA.module.css';

/** Marca «Generado por IA» junto al chip de origen. No dibuja nada si la fuente no es IA. */
export function EtiquetaIA({ source }: { source?: string }) {
  if (!esFuenteIA(source)) return null;
  return <span className={styles.ia} title="Lo generó una IA: revisalo antes de exportar">Generado por IA</span>;
}

/** Aviso de un campo `suggested`: «Aceptar» lo pasa a manual conservando valor y fuente. */
export function AvisoSugerido({ nombre, source, onAceptar }: { nombre: string; source?: string; onAceptar: () => void }) {
  return (
    <div aria-label={`Sugerencia de ${nombre}`} className={styles.aviso} role="group">
      <span className={styles.texto}>
        {source ? `${source} sugiere ${nombre}` : `Hay ${nombre} sugerido`} — revisalo y aceptalo si te sirve.
      </span>
      <DosButton onClick={onAceptar} size="sm" variant="primary">Aceptar</DosButton>
    </div>
  );
}
