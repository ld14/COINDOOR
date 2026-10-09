import styles from './OriginChip.module.css';

export type OriginStatus = 'manual' | 'suggested' | 'empty';

interface OriginChipProps {
  /** Muestra la etiqueta OBLIGATORIO junto al chip de un campo vacío que bloquea la exportación. */
  required?: boolean;
  /** Fuente del dato (`arcadedb`, `mame`, `manual`…). Solo importa si status es `manual`. */
  source?: string;
  status?: OriginStatus;
}

const SOURCE_NAMES: Record<string, string> = {
  arcadedb: 'ArcadeDB',
  mame: 'MAME',
  screenscraper: 'ScreenScraper',
};

function isExternal(source?: string): boolean {
  const key = source?.trim().toLowerCase();
  return !!key && key !== 'manual';
}

/** Texto visible del chip según DESIGN_SPEC §3. */
function originLabel(status: OriginStatus, source?: string): string {
  if (status === 'empty') return '○ Vacío';
  if (status === 'suggested') return '● Sugerido · sin revisar';
  if (!isExternal(source)) return '● Manual';
  const clean = source!.trim();
  return `● ${SOURCE_NAMES[clean.toLowerCase()] ?? clean}`;
}

export function OriginChip({ required = false, source, status = 'empty' }: OriginChipProps) {
  const kind = status === 'manual' ? (isExternal(source) ? styles.external : styles.manual) : styles[status];
  return (
    <span className={styles.wrap}>
      <span className={[styles.chip, kind].join(' ')}>{originLabel(status, source)}</span>
      {status === 'empty' && required ? <span className={styles.required}>OBLIGATORIO</span> : null}
    </span>
  );
}
