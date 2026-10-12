import { useState } from 'react';
import { Card, DosButton, OriginChip } from '@/components/dos';
import { Dropzone } from '@/components/dos/entrada';
import { YoutubeDownload } from '@/components/YoutubeDownload';
import { FIELDDEFS } from '@/lib/domain/types';
import type { Game, ImageKey, VideoKey } from '@/lib/domain/types';
import { useFichaAutosave } from './autosaveContext';
import { confirmManualDelete } from './helpers';
import styles from './VideoSection.module.css';

const SUGERIR = 'Sugerir desde ArcadeDB';

export function VideoSection({ game, onDelete, onSuggestVideo, onUpload }: {
  game: Game;
  onDelete: (key: ImageKey | VideoKey) => void;
  onSuggestVideo: () => void;
  onUpload: (key: ImageKey | VideoKey, file: File) => void;
}) {
  const { aceptar } = useFichaAutosave();
  // Un reemplazo escribe el mismo video.mp4: sin cambiar el src, el reproductor
  // seguiría mostrando el archivo viejo desde la caché.
  const [version, setVersion] = useState(0);
  const [field] = FIELDDEFS.videos;
  const video = game.video[field.key];
  const status = video?.status ?? 'empty';
  const aceptada = status === 'manual' && !!video?.source && video.source.trim().toLowerCase() !== 'manual';
  const clase = [styles.box, status === 'suggested' ? styles.suggested : ''].filter(Boolean).join(' ');

  return (
    <Card
      actions={(
        <button aria-label={`Sugerir ${field.label}`} className={styles.suggest} onClick={onSuggestVideo} title={SUGERIR} type="button">
          ↻
        </button>
      )}
      band="var(--accent-3)"
      bandInk="var(--ink-on-accent)"
      hint=".mp4 o descarga desde YouTube"
      number={5}
      title="Video"
    >
      <div aria-label={field.label} className={clase} data-campo={field.key} role="group">
        <div className={styles.head}>
          <span className={styles.name}>{field.label}</span>
          <OriginChip source={video?.source} status={status} />
          {aceptada ? <span className={styles.accepted}>✓ Aceptado</span> : null}
        </div>
        <div className={styles.preview}>
          {video?.url ? (
            <video
              className={styles.player}
              controls
              preload="metadata"
              src={version ? `${video.url}?v=${version}` : video.url}
            />
          ) : `${field.label.toLowerCase()} · ${field.ratio} · No Disponible`}
        </div>
        {status === 'suggested' ? (
          <div className={styles.actions}>
            <DosButton onClick={() => aceptar(field.key)} size="sm" variant="primary">✓ Aceptar</DosButton>
            <DosButton onClick={onSuggestVideo} size="sm" variant="ghost">Cambiar</DosButton>
          </div>
        ) : null}
        <div className={styles.sources}>
          <Dropzone
            accept="video/mp4,.mp4"
            label={video?.url ? 'Soltá otro .mp4 para reemplazar' : 'Soltá un video .mp4 acá'}
            onFile={(file) => onUpload(field.key, file)}
          />
          <YoutubeDownload
            current={video}
            gameId={game.id}
            onDownloaded={() => setVersion(Date.now())}
          />
        </div>
        {status !== 'empty' ? (
          <div className={styles.actions}>
            <DosButton onClick={() => confirmManualDelete(status, () => onDelete(field.key))} size="sm" variant="danger">Borrar</DosButton>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
