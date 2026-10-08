import { type ReactNode, useState } from 'react';
import { DosButton, FieldTag, Panel, SectionHeader } from '@/components/dos';
import { ImageModal } from '@/components/ImageModal';
import { GalleryPanel } from '@/components/GalleryPanel';
import { YoutubeDownload } from '@/components/YoutubeDownload';
import { FIELDDEFS } from '@/lib/domain/types';
import type { Game, ImageKey, MediaField, VideoKey } from '@/lib/domain/types';
import { confirmManualDelete } from './helpers';
import styles from '../ReadPages.module.css';

export function MediaSection({
  game,
  onDelete,
  onSuggestVideo,
  onSuggestImage,
  onUpload,
  onGalleryChanged,
}: {
  game: Game;
  onDelete: (key: ImageKey | VideoKey) => void;
  onSuggestVideo: () => void;
  onSuggestImage: (key: ImageKey) => void;
  onUpload: (key: ImageKey | VideoKey, file: File) => void;
  onGalleryChanged: () => void;
}) {
  // Un reemplazo escribe el mismo video.mp4: sin cambiar el src, el reproductor
  // seguiría mostrando el archivo viejo desde la caché.
  const [videoVersion, setVideoVersion] = useState(0);

  return (
    <>
      <Panel>
        <SectionHeader>IMÁGENES</SectionHeader>
        <div className={styles.mediaGrid}>
          {FIELDDEFS.images.map((field) => (
            <MediaCard
              field={game.images[field.key]}
              key={field.key}
              label={field.label}
              mediaKey={field.key}
              onDelete={onDelete}
              onSuggest={() => onSuggestImage(field.key)}
              onUpload={onUpload}
              ratio={field.ratio}
            />
          ))}
        </div>
      </Panel>
      <GalleryPanel gallery={game.gallery ?? []} gameId={game.id} onChanged={onGalleryChanged} />
      <Panel>
        <SectionHeader>VIDEO</SectionHeader>
        <div className={styles.mediaGrid}>
          {FIELDDEFS.videos.map((field) => (
            <MediaCard
              field={game.video[field.key]}
              key={field.key}
              label={field.label}
              mediaKey={field.key}
              onDelete={onDelete}
              onSuggest={onSuggestVideo}
              onUpload={onUpload}
              ratio={field.ratio}
              version={videoVersion}
            >
              <YoutubeDownload
                current={game.video[field.key]}
                gameId={game.id}
                onDownloaded={() => setVideoVersion(Date.now())}
              />
            </MediaCard>
          ))}
        </div>
      </Panel>
    </>
  );
}

function MediaCard({
  children,
  field,
  label,
  mediaKey,
  onDelete,
  onSuggest,
  onUpload,
  ratio,
  version,
}: {
  children?: ReactNode;
  field?: MediaField;
  label: string;
  mediaKey: ImageKey | VideoKey;
  onDelete: (key: ImageKey | VideoKey) => void;
  onSuggest?: () => void;
  onUpload: (key: ImageKey | VideoKey, file: File) => void;
  ratio: string;
  version?: number;
}) {
  const [imageModalOpen, setImageModalOpen] = useState(false);
  const status = field?.status ?? 'empty';
  const isVideo = mediaKey === 'video';

  return (
    <Panel className={styles.stack}>
      <div className={styles.fieldTop}>
        <span className={styles.name}>{label}</span>
        <FieldTag status={status} />
      </div>
      <div className={styles.preview}>
        {field?.url ? (
          isVideo ? (
            <video
              className={styles.videoPlayer}
              controls
              preload="metadata"
              src={version ? `${field.url}?v=${version}` : field.url}
            />
          ) : (
            <button
              className={styles.imageButton}
              onClick={() => setImageModalOpen(true)}
              type="button"
            >
              <img alt={label} className={styles.previewImage} src={field.url} />
            </button>
          )
        ) : `${label.toLowerCase()} · ${ratio} · No Disponible`}
      </div>
      <input
        aria-label={`Cargar ${label}`}
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onUpload(mediaKey, file);
        }}
        type="file"
      />
      <div className={styles.toolbar}>
        {onSuggest ? <DosButton onClick={onSuggest} variant="ghost-small">Sugerir</DosButton> : null}
        {status !== 'empty' ? (
          <DosButton onClick={() => confirmManualDelete(status, () => onDelete(mediaKey))} variant="danger-small">Borrar</DosButton>
        ) : null}
      </div>
      {children}
      {!isVideo && field?.url ? (
        <ImageModal
          alt={label}
          onClose={() => setImageModalOpen(false)}
          open={imageModalOpen}
          src={field.url}
        />
      ) : null}
    </Panel>
  );
}
