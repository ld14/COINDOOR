import { useEffect, useRef, useState } from 'react';
import { Card, DosButton, OriginChip } from '@/components/dos';
import { Dropzone } from '@/components/dos/entrada';
import { ImageModal } from '@/components/ImageModal';
import type { SuggestionCandidate } from '@/lib/api/suggestions';
import { FIELDDEFS } from '@/lib/domain/types';
import type { Game, ImageKey, MediaField, VideoKey } from '@/lib/domain/types';
import { useFichaAutosave } from './autosaveContext';
import { confirmManualDelete } from './helpers';
import styles from './ImagenesSection.module.css';

const SUGERIR = 'Sugerir desde ArcadeDB';
/** Si una aceptación no se refleja en la ficha (falló), se sigue con la próxima pasado este tiempo. */
const ESPERA_ACEPTAR_MS = 10000;

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
  const { aceptar } = useFichaAutosave();
  const sugeridas = FIELDDEFS.images.filter((f) => game.images[f.key]?.status === 'suggested').map((f) => f.key);
  const cargadas = FIELDDEFS.images.filter((f) => (game.images[f.key]?.status ?? 'empty') !== 'empty').length;

  // "Aceptar las N": de a una, esperando que la ficha refleje cada aceptación (cada una reescribe el game.json).
  const [cola, setCola] = useState<string[]>([]);
  const emitida = useRef<string | null>(null);
  useEffect(() => {
    if (cola.length === 0) {
      emitida.current = null;
      return undefined;
    }
    const cabeza = cola[0];
    if (emitida.current !== cabeza) {
      emitida.current = cabeza;
      aceptar(cabeza);
    }
    if (game.images[cabeza as ImageKey]?.status !== 'suggested') {
      setCola((actual) => actual.slice(1));
      return undefined;
    }
    const espera = setTimeout(() => setCola((actual) => actual.slice(1)), ESPERA_ACEPTAR_MS);
    return () => clearTimeout(espera);
  }, [cola, game.images, aceptar]);

  return (
    <Card
      actions={sugeridas.length > 0 ? (
        <DosButton disabled={cola.length > 0} onClick={() => setCola(sugeridas)} size="sm" variant="ghost">
          ✓ Aceptar las {sugeridas.length}
        </DosButton>
      ) : undefined}
      band="var(--accent-2)"
      bandInk="var(--ink-on-accent-2)"
      hint={`${cargadas} de ${FIELDDEFS.images.length} · arrastrá para reemplazar`}
      number={2}
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
            onAccept={() => aceptar(field.key)}
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

function ImageSlot({ field, label, mediaKey, onAccept, onDelete, onSuggest, onUpload, ratio, required }: {
  field?: MediaField;
  label: string;
  mediaKey: ImageKey;
  onAccept: () => void;
  onDelete: (key: ImageKey) => void;
  onSuggest: () => void;
  onUpload: (key: ImageKey, file: File) => void;
  ratio: string;
  required: boolean;
}) {
  const [imageModalOpen, setImageModalOpen] = useState(false);
  const status = field?.status ?? 'empty';
  const bloquea = status === 'empty' && required;
  const aceptada = status === 'manual' && !!field?.source && field.source.trim().toLowerCase() !== 'manual';
  const clase = [styles.slot, status === 'suggested' ? styles.suggested : '', bloquea ? styles.blocking : ''].filter(Boolean).join(' ');

  return (
    <div aria-label={label} className={clase} data-campo={mediaKey} role="group">
      <div className={styles.head}>
        <span className={styles.name}>{label}</span>
      </div>
      <OriginChip required={bloquea} source={field?.source} status={status} />
      <button aria-label={`Sugerir ${label}`} className={styles.suggest} onClick={onSuggest} title={SUGERIR} type="button">↻</button>
      <div className={styles.preview}>
        {field?.url ? (
          <button className={styles.imageButton} onClick={() => setImageModalOpen(true)} type="button">
            <img alt={label} className={styles.image} src={field.url} />
          </button>
        ) : `${label.toLowerCase()} · ${ratio} · No Disponible`}
      </div>
      {bloquea ? <span className={styles.blocks}>✕ Bloquea la exportación</span> : null}
      {status === 'suggested' ? (
        <div className={styles.actions}>
          <DosButton onClick={onAccept} size="sm" variant="primary">✓ Aceptar</DosButton>
          <DosButton onClick={onSuggest} size="sm" variant="ghost">Cambiar</DosButton>
        </div>
      ) : null}
      {aceptada ? <span className={styles.accepted}>✓ Aceptada</span> : null}
      <Dropzone
        accept="image/*"
        label={field?.url ? 'Soltá otra imagen para reemplazar' : 'Soltá una imagen acá o pegala con Ctrl+V'}
        onFile={(file) => onUpload(mediaKey, file)}
      />
      {status !== 'empty' ? (
        <DosButton onClick={() => confirmManualDelete(status, () => onDelete(mediaKey))} size="sm" variant="danger">Borrar</DosButton>
      ) : null}
      {field?.url ? (
        <ImageModal alt={label} onClose={() => setImageModalOpen(false)} open={imageModalOpen} src={field.url} />
      ) : null}
    </div>
  );
}
