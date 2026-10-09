import { Card, DosButton, DosSelect, ProgressBar, StatusBadge } from '@/components/dos';
import { useDominantColors } from '@/hooks/useDominantColors';
import type { FichaProgress, PendienteFicha } from '@/hooks/useFichaProgress';
import type { computeGameStatus } from '@/lib/domain/completeness';
import type { Game, System } from '@/lib/domain/types';
import { useProximoAcento } from './acentoSlot';
import styles from './ficha.module.css';

export interface FichaHeroProps {
  game: Game;
  systems: System[];
  status: ReturnType<typeof computeGameStatus>;
  progress: FichaProgress;
  /** Obsoleto: el slot sale de `acentoSlot`, compartido con Presentación. */
  proximoAcento?: unknown;
  onSystemChange: (systemId: string) => void;
  onMarkReady: () => void;
  /** Clic en una píldora "✕ obligatorio": lleva al campo. */
  onGoPendiente: (pendiente: PendienteFicha) => void;
  onPickColor: (hex: string) => void;
}

function nombreDeArchivo(romRef: string): string {
  return romRef.split(/[\\/]/).pop() || romRef;
}

/** Línea de metadatos: año · desarrollador · editor · género · jugadores. */
function metadatos(game: Game): string {
  const { year, developer, publisher, genre, players } = game.identity;
  return [year, developer, publisher, genre, players ? `${players} jugadores` : ''].filter((valor) => valor.trim() !== '').join(' · ');
}

export function FichaHero({ game, systems, status, progress, onSystemChange, onMarkReady, onGoPendiente, onPickColor }: FichaHeroProps) {
  const coverUrl = game.images.caratula?.url;
  const heroMedia = coverUrl ?? game.video.video?.url;
  const { colors } = useDominantColors(coverUrl, 4);
  const sistema = systems.find((s) => s.id === game.systemId);
  const archivo = game.romRef ? nombreDeArchivo(game.romRef) : '';
  const meta = metadatos(game);
  const { percent, faltantes } = progress;
  const proximoAcento = useProximoAcento();
  const slot = proximoAcento === 0 ? 'primario' : 'secundario';

  return (
    <Card className={styles.hero}>
      <div className={styles.cover}>
        {heroMedia
          ? <img alt={game.identity.title} className={styles.coverImg} src={heroMedia} />
          : <span className={styles.coverVacia}>{`${game.identity.title} · carátula pendiente`}</span>}
      </div>
      <div className={styles.heroInfo}>
        <div className={styles.heroBadges}>
          <StatusBadge status={status} />
          <span className={styles.sysChip}>{[sistema?.shortName ?? game.systemId, archivo].filter(Boolean).join(' · ')}</span>
        </div>
        <h1 className={styles.title}>{game.identity.title}</h1>
        {meta ? <p className={styles.heroMeta}>{meta}</p> : null}

        <div className={styles.progreso}>
          <ProgressBar label="Completitud de la ficha" state={percent === 100 ? 'ok' : 'active'} value={percent} />
          <span className={styles.progresoTexto}>
            <strong>{`${percent}% completo`}</strong>
            {faltantes.length > 0 ? ` · faltan ${faltantes.length}` : ' · listo para revisar'}
          </span>
        </div>

        <div className={styles.faltan}>
          {faltantes.length > 0 ? (
            <>
              <span className={styles.faltanRotulo}>Para exportar falta:</span>
              <ul aria-label="Obligatorios que faltan" className={styles.pildoras}>
                {faltantes.map((p) => (
                  <li key={p.id}>
                    <button className={styles.pildora} onClick={() => onGoPendiente(p)} type="button">
                      <span aria-hidden="true">✕</span>
                      {` ${p.label}`}
                    </button>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <span className={styles.faltanOk}>✓ Los obligatorios están completos.</span>
          )}
        </div>

        <div className={styles.heroAcciones}>
          <DosSelect aria-label="Plataforma" className={styles.systemSelect} onChange={(e) => onSystemChange(e.target.value)} value={game.systemId}>
            {systems.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </DosSelect>
          <DosButton onClick={onMarkReady} variant="ghost-small">Marcar como listo</DosButton>
        </div>

        {colors.length > 0 ? (
          <div className={styles.paleta}>
            <span className={styles.paletaRotulo}>
              Colores predominantes
              <span className={styles.meta}>{` — clic: acento ${slot}`}</span>
            </span>
            <div className={styles.muestras}>
              {colors.map((color) => (
                <button
                  aria-label={`Usar ${color.hex} como acento ${slot}`}
                  className={styles.muestra}
                  key={color.hex}
                  onClick={() => onPickColor(color.hex)}
                  type="button"
                >
                  <span className={styles.muestraColor} style={{ backgroundColor: color.hex }} />
                  <span className={styles.muestraHex}>{color.hex}</span>
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
