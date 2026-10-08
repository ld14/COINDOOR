import { Panel, ProgressBar, SectionHeader, SunkenBox } from '@/components/dos';
import type { Game } from '@/lib/domain/types';
import styles from '../ReadPages.module.css';

export function CompletionDashboard({ game, missing }: { game: Game; missing: string[] }) {
  const tiles = buildCompletionTiles(game, missing);
  const complete = tiles.filter((tile) => tile.state === 'complete').length;
  const progress = Math.round((complete / tiles.length) * 100);
  return (
    <Panel>
      <SectionHeader>DASHBOARD DE COMPLETITUD</SectionHeader>
      <SunkenBox className={styles.completionPanel}>
        <div className={styles.completionHeader}>
          <span className={styles.name}>{progress}% completo</span>
          <span className={styles.meta}>{missing.length ? `${missing.length} pendiente(s)` : 'listo para revisar'}</span>
        </div>
        <ProgressBar value={progress} />
        <div className={styles.completionGrid}>
          {tiles.map((tile) => (
            <div className={styles.completionTile} key={tile.label}>
              <span className={styles.tileMark}>{tile.state === 'complete' ? '✓' : tile.state === 'error' ? 'X' : '○'}</span>
              <span className={styles.name}>{tile.label}</span>
              <span className={styles.meta}>{tile.detail}</span>
            </div>
          ))}
        </div>
        {missing.length ? (
          <div className={styles.criticalList}>
            {missing.slice(0, 4).map((item) => <span key={item}>- {item}</span>)}
            {missing.length > 4 ? <span>+ {missing.length - 4} más</span> : null}
          </div>
        ) : null}
      </SunkenBox>
    </Panel>
  );
}

type CompletionTile = {
  label: string;
  state: 'complete' | 'pending' | 'error';
  detail: string;
};

function buildCompletionTiles(game: Game, missing: string[]): CompletionTile[] {
  const missingText = missing.join(' ');
  const mediaReady = game.images.caratula?.status !== 'empty' && game.images.poster?.status !== 'empty';
  const optionalCount = [game.images.marquesina, game.images.logo, game.images.captura, game.video.video, game.review, game.cheats].filter((field) => field?.status !== 'empty').length;
  return [
    { label: 'Identidad', state: missingText.includes('Identidad') ? 'pending' : 'complete', detail: missingText.includes('Identidad') ? 'faltan datos base' : 'base completa' },
    { label: 'Media obligatoria', state: mediaReady ? 'complete' : 'pending', detail: mediaReady ? 'carátula + póster' : 'faltan assets clave' },
    { label: 'Textos', state: game.texts.sinopsis.status === 'empty' ? 'pending' : 'complete', detail: game.texts.sinopsis.status === 'empty' ? 'sin sinopsis' : 'sinopsis cargada' },
    { label: 'Presentación', state: game.accent === 'empty' ? 'pending' : 'complete', detail: game.accent === 'empty' ? 'sin color' : 'color definido' },
    { label: 'Opcionales', state: optionalCount > 0 ? 'complete' : 'pending', detail: `${optionalCount} cargado(s)` },
  ];
}
