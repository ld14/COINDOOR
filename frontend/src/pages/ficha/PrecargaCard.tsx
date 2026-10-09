import { Card, DosButton } from '@/components/dos';
import styles from './ficha.module.css';

interface PrecargaCardProps {
  /** `arcade` busca en ArcadeDB; `msdos` en LaunchBox + IA. */
  tipo: 'arcade' | 'msdos';
  cargando: boolean;
  onPrecargar: () => void;
}

const TEXTOS = {
  arcade: {
    titulo: 'PRECARGA DE ARCADEDB',
    ayuda: 'Buscar datos del juego en Arcade Database (identidad, imágenes, sinopsis, trucos, gabinete).',
    boton: 'Precargar ArcadeDB',
  },
  msdos: {
    titulo: 'PRECARGA DE MSDOS',
    ayuda: 'Buscar datos del juego en Launchbox + IA (año, imágenes, identidad, sinopsis).',
    boton: 'Precargar Launchbox + IA',
  },
} as const;

/** Lanzador de la precarga (columna lateral). Mientras corre el job se oculta y el progreso va en el banner. */
export function PrecargaCard({ tipo, cargando, onPrecargar }: PrecargaCardProps) {
  const texto = TEXTOS[tipo];
  return (
    <Card band="var(--accent-2)" title={texto.titulo}>
      <div className={styles.stack}>
        <p className={styles.meta}>{texto.ayuda}</p>
        <div>
          <DosButton disabled={cargando} onClick={onPrecargar} variant="primary-small">
            {cargando ? 'Iniciando…' : texto.boton}
          </DosButton>
        </div>
      </div>
    </Card>
  );
}
