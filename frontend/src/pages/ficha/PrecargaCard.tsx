import { Card, DosButton } from '@/components/dos';
import styles from './ficha.module.css';

interface PrecargaCardProps {
  cargando: boolean;
  onPrecargar: () => void;
}

/** Lanzador del completado (columna lateral). Mientras corre el job se oculta y el progreso va en el banner. */
export function PrecargaCard({ cargando, onPrecargar }: PrecargaCardProps) {
  return (
    <Card band="var(--accent-2)" title="COMPLETAR LA FICHA">
      <div className={styles.stack}>
        <p className={styles.meta}>Busca en todas las fuentes lo que falta: identidad, textos, imágenes, reseña y trucos. Lo que ya está cargado no se toca.</p>
        <div>
          <DosButton disabled={cargando} onClick={onPrecargar} variant="primary-small">
            {cargando ? 'Iniciando…' : 'Completar lo que falta'}
          </DosButton>
        </div>
      </div>
    </Card>
  );
}
