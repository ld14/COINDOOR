import { useState } from 'react';
import { Card, OriginChip } from '@/components/dos';
import { Dropzone } from '@/components/dos/entrada';
import { ImageModal } from '@/components/ImageModal';
import type { SuggestionCandidate } from '@/lib/api/suggestions';
import { FIELDDEFS } from '@/lib/domain/types';
import type { Game, ImageKey, MediaField, VideoKey } from '@/lib/domain/types';
import { confirmManualDelete } from './helpers';
import styles from './ImagenesSection.module.css';

const SUGERIR = 'Sugerir desde ArcadeDB';

/** Candidatas de un slot de imagen, buscadas por el orquestador (esta sección no llama a la API). */
export interface CandidatasImagen {
  key: ImageKey;
  candidatos: SuggestionCandidate[];
}

interface ImagenesSectionProps {
  game: Game;
  onDelete: (key: ImageKey | VideoKey) => void;
  onSuggestImage: (key: ImageKey) => void;
  onUpload: (key: ImageKey | VideoKey, file: File) => void;
  /** Fila «N opciones — elegí una»; solo aparece con dos o más candidatas aplicables. */
  candidatas?: CandidatasImagen | null;
  onPickCandidata?: (key: ImageKey, candidateId: string) => void;
}

/** Las candidatas que se pueden aplicar con un clic: tienen miniatura y no son solo una referencia. */
function aplicables(candidatas?: CandidatasImagen | null): SuggestionCandidate[] {
  return (candidatas?.candidatos ?? []).filter((c) => c.kind === 'media' && c.clase === 'aplicable' && (c.previewUrl || c.mediaUrl));
}

function FilaCandidatas({ candidatas, field, label, onPick, onUpload }: {
  candidatas: CandidatasImagen;
  field?: MediaField;
  label: string;
  onPick: (candidateId: string) => void;
  onUpload: (file: File) => void;
}) {
  const lista = aplicables(candidatas);
  const fuentes = [...new Set(lista.map((c) => c.fuente))];
  const origen = fuentes.length === 1 ? fuentes[0] : 'Las fuentes';
  // Resalta la que la precarga dejó puesta (misma fuente que el slot), nunca una a ojo.
  const elegida = field?.source ? lista.find((c) => c.fuente === field.source)?.id : undefined;
  return (
    <div aria-label={`Opciones de ${label}`} className={styles.cands} role="group">
      <p className={styles.candsHead}><b>{label}</b> · {origen} encontró {lista.length} opciones — elegí una</p>
      <div className={styles.candsRow}>
        {lista.map((c) => (
          <button
            aria-label={`Usar la opción de ${c.fuente}`}
            aria-pressed={c.id === elegida}
            className={[styles.cand, c.id === elegida ? styles.candSel : ''].filter(Boolean).join(' ')}
            key={c.id}
            onClick={() => onPick(c.id)}
            type="button"
          >
            <img alt="" className={styles.candThumb} src={c.previewUrl ?? c.mediaUrl ?? ''} />
            <span>{c.fuente}</span>
          </button>
        ))}
        <div className={styles.candDrop}>
          <b>Usar la mía</b>
          <Dropzone accept="image/*" label="Soltá o pegá con Ctrl+V" onFile={onUpload} />
        </div>
      </div>
    </div>
  );
}

export function ImagenesSection({ game, onDelete, onSuggestImage, onUpload, candidatas, onPickCandidata }: ImagenesSectionProps) {
  const cargadas = FIELDDEFS.images.filter((f) => (game.images[f.key]?.status ?? 'empty') !== 'empty').length;

  return (
    <Card
      band="var(--accent-2)"
      bandInk="var(--ink-on-accent-2)"
      hint={`${cargadas} de ${FIELDDEFS.images.length} · arrastrá para reemplazar`}
      number={3}
      title="Imágenes"
    >
      {candidatas && aplicables(candidatas).length >= 2 ? (
        <FilaCandidatas
          candidatas={candidatas}
          field={game.images[candidatas.key]}
          label={FIELDDEFS.images.find((f) => f.key === candidatas.key)?.label ?? candidatas.key}
          onPick={(id) => onPickCandidata?.(candidatas.key, id)}
          onUpload={(file) => onUpload(candidatas.key, file)}
        />
      ) : null}
      <div className={styles.grid}>
        {FIELDDEFS.images.map((field) => (
          <ImageSlot
            field={game.images[field.key]}
            key={field.key}
            label={field.label}
            mediaKey={field.key}
            onDelete={onDelete}
            onSuggest={() => onSuggestImage(field.key)}
            onUpload={onUpload}
            ratio={field.ratio}
            required={field.required}
          />
        ))}
      </div>
    </Card>
  );
}

function ImageSlot({ field, label, mediaKey, onDelete, onSuggest, onUpload, ratio, required }: {
  field?: MediaField;
  label: string;
  mediaKey: ImageKey;
  onDelete: (key: ImageKey) => void;
  onSuggest: () => void;
  onUpload: (key: ImageKey, file: File) => void;
  ratio: string;
  required: boolean;
}) {
  const [imageModalOpen, setImageModalOpen] = useState(false);
  // Una imagen cargada ya cuenta como aceptada: no pide validación (aunque venga de una fuente).
  const estado = field?.status ?? 'empty';
  const status = estado === 'suggested' && field?.url ? 'manual' : estado;
  const bloquea = status === 'empty' && required;
  const aceptada = status === 'manual' && !!field?.source && field.source.trim().toLowerCase() !== 'manual';
  const clase = [styles.slot, bloquea ? styles.blocking : ''].filter(Boolean).join(' ');

  return (
    <div aria-label={label} className={clase} data-campo={mediaKey} role="group">
      <div className={styles.head}>
        <span className={styles.name}>{label}</span>
      </div>
      <OriginChip required={bloquea} source={field?.source} status={status} />
      <div className={styles.preview}>
        {field?.url ? (
          <button className={styles.imageButton} onClick={() => setImageModalOpen(true)} type="button">
            <img alt={label} className={styles.image} src={field.url} />
          </button>
        ) : `${label.toLowerCase()} · ${ratio} · No Disponible`}
      </div>
      {bloquea ? <span className={styles.blocks}>✕ Bloquea la exportación</span> : null}
      <div className={styles.pie}>
        <div className={styles.actions}>
          <button aria-label={`Sugerir ${label}`} className={styles.suggest} onClick={onSuggest} title={SUGERIR} type="button">↻</button>
          {status !== 'empty' ? (
            <button aria-label={`Borrar ${label}`} className={styles.borrar} onClick={() => confirmManualDelete(status, () => onDelete(mediaKey))} title="Borrar" type="button">
              <svg aria-hidden="true" fill="none" height="16" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" width="16"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14M10 11v6M14 11v6" /></svg>
            </button>
          ) : null}
        </div>
        {aceptada ? <span className={styles.accepted}>✓ Aceptada</span> : null}
        <div className={styles.carga}>
          <Dropzone
            accept="image/*"
            compact
            label={field?.url ? 'Reemplazar imagen' : 'Subir imagen'}
            onFile={(file) => onUpload(mediaKey, file)}
          />
        </div>
      </div>
      {field?.url ? (
        <ImageModal alt={label} onClose={() => setImageModalOpen(false)} open={imageModalOpen} src={field.url} />
      ) : null}
    </div>
  );
}
