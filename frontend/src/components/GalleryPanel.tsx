import { useCallback, useEffect, useState } from 'react';
import { DosButton, DosSelect, Modal, Panel, SectionHeader, Spinner, SunkenBox } from '@/components/dos';
import { ImageModal } from '@/components/ImageModal';
import {
  deleteGalleryImage,
  listGalleryCandidates,
  saveGallery,
  useGalleryImageAs,
  type GalleryCandidate,
  type GuardarGaleriaItem,
} from '@/lib/api/gallery';
import { getJob } from '@/lib/api/jobs';
import { FIELDDEFS } from '@/lib/domain/types';
import type { GalleryImage, ImageKey } from '@/lib/domain/types';
import styles from '@/pages/ReadPages.module.css';

interface GalleryPanelProps {
  gameId: string;
  gallery: GalleryImage[];
  onChanged: () => void;
}

export function GalleryPanel({ gameId, gallery, onChanged }: GalleryPanelProps) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [error, setError] = useState('');

  return (
    <Panel>
      <SectionHeader>GALERÍA</SectionHeader>
      <SunkenBox className={styles.stack}>
        <p className={styles.meta}>
          Banco de imágenes de ArcadeDB, ImageSearch y Launchbox, aparte de los campos del
          contrato. Viaja en el paquete si la tildás al exportar.
        </p>
        {error ? <p className={styles.error}>{error}</p> : null}
        {gallery.length === 0 ? (
          <p className={styles.empty}>No Disponible</p>
        ) : (
          <div className={styles.galleryGrid}>
            {gallery.map((imagen) => (
              <GalleryItem
                gameId={gameId}
                imagen={imagen}
                key={imagen.id}
                onChanged={onChanged}
                onError={setError}
              />
            ))}
          </div>
        )}
        <div className={styles.toolbar}>
          <DosButton onClick={() => setPickerOpen(true)} variant="primary-small">
            Traer de imágenes
          </DosButton>
        </div>
      </SunkenBox>
      {pickerOpen ? (
        <GalleryPicker
          gameId={gameId}
          onClose={() => setPickerOpen(false)}
          onSaved={() => {
            setPickerOpen(false);
            onChanged();
          }}
        />
      ) : null}
    </Panel>
  );
}

function GalleryItem({
  gameId,
  imagen,
  onChanged,
  onError,
}: {
  gameId: string;
  imagen: GalleryImage;
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [ampliada, setAmpliada] = useState(false);
  const [ocupado, setOcupado] = useState(false);

  const correr = async (accion: () => Promise<unknown>) => {
    setOcupado(true);
    try {
      await accion();
      onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : 'No se pudo completar la acción.');
    } finally {
      setOcupado(false);
    }
  };

  return (
    <div className={styles.galleryItem}>
      <div className={styles.galleryThumb}>
        <button
          className={styles.imageButton}
          onClick={() => setAmpliada(true)}
          type="button"
        >
          <img alt={imagen.label} className={styles.previewImage} src={imagen.url} />
        </button>
      </div>
      <span className={styles.name}>{imagen.label}</span>
      <span className={styles.galleryBadge}>{imagen.source}</span>
      <DosSelect
        aria-label={`Usar ${imagen.label} como`}
        disabled={ocupado}
        onChange={(event) => {
          const campo = event.target.value as ImageKey;
          if (campo) void correr(() => useGalleryImageAs(gameId, imagen.id, campo));
          event.target.value = '';
        }}
        value=""
      >
        <option value="">Usar como…</option>
        {FIELDDEFS.images.map((field) => (
          <option key={field.key} value={field.key}>{field.label}</option>
        ))}
      </DosSelect>
      <DosButton
        disabled={ocupado}
        onClick={() => void correr(() => deleteGalleryImage(gameId, imagen.id))}
        variant="danger-small"
      >
        Borrar
      </DosButton>
      <ImageModal
        alt={imagen.label}
        onClose={() => setAmpliada(false)}
        open={ampliada}
        src={imagen.url}
      />
    </div>
  );
}

function GalleryPicker({
  gameId,
  onClose,
  onSaved,
}: {
  gameId: string;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [candidatos, setCandidatos] = useState<GalleryCandidate[] | null>(null);
  const [elegidos, setElegidos] = useState<Set<string>>(new Set());
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');
  const [retrying, setRetrying] = useState<string | null>(null);

  const cargar = (source?: string) => {
    listGalleryCandidates(gameId, source)
      .then((nuevos) => {
        if (source) {
          // Agregar o reemplazar candidatos de esa fuente
          setCandidatos((prev) => {
            if (!prev) return nuevos;
            const sinFuente = prev.filter((c) => c.source !== source);
            return [...sinFuente, ...nuevos];
          });
        } else {
          setCandidatos(nuevos);
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'No se pudieron traer las imágenes.'));
  };

  useEffect(() => { cargar(); }, [gameId]);

  const reintentar = async (source: string) => {
    setRetrying(source);
    setError('');
    try {
      await new Promise((r) => setTimeout(r, 300)); // pausa visual
      cargar(source);
    } finally {
      setRetrying(null);
    }
  };

  const alternar = useCallback((id: string) => {
    setElegidos((previo) => {
      const siguiente = new Set(previo);
      if (siguiente.has(id)) siguiente.delete(id);
      else siguiente.add(id);
      return siguiente;
    });
  }, []);

  // Sólo lo que todavía no está guardado: retildar algo ya bajado lo duplicaría.
  const disponibles = (candidatos ?? []).filter((c) => !c.yaGuardada);
  const todosElegidos = disponibles.length > 0 && disponibles.every((c) => elegidos.has(c.id));

  async function guardar() {
    setGuardando(true);
    setError('');
    try {
      const items: GuardarGaleriaItem[] = disponibles
        .filter((c) => elegidos.has(c.id))
        .map((c) => {
          if (c.source === 'ArcadeDB' || c.source === 'ArcadeDB (romset padre)') {
            return { tipo: c.tipo, source: c.source };
          }
          return { url: c.url, source: c.source };
        });
      const { jobId } = await saveGallery(gameId, items);
      await esperarJob(jobId);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudieron guardar las imágenes.');
      setGuardando(false);
    }
  }

  // Agrupar candidatos por fuente, incluyendo fuentes sin resultados
  const TODAS_LAS_FUENTES = ['ArcadeDB', 'ImageSearch', 'Launchbox'];
  const porFuente = new Map<string, GalleryCandidate[]>();
  for (const fuente of TODAS_LAS_FUENTES) {
    porFuente.set(fuente, []);
  }
  for (const c of disponibles) {
    const lista = porFuente.get(c.source) ?? [];
    lista.push(c);
    porFuente.set(c.source, lista);
  }

  return (
    <Modal onClose={onClose} open size="large" title="Imágenes disponibles">
      <div className={styles.stack}>
        {error ? <p className={styles.error}>{error}</p> : null}
        {candidatos === null ? (
          <Spinner />
        ) : candidatos.length === 0 ? (
          <p className={styles.empty}>No se encontraron imágenes para este juego.</p>
        ) : (
          <>
            <div className={styles.toolbar}>
              <DosButton
                onClick={() => setElegidos(todosElegidos ? new Set() : new Set(disponibles.map((c) => c.id)))}
                variant="ghost-small"
              >
                {todosElegidos ? 'Ninguna' : 'Seleccionar todo'}
              </DosButton>
              <span className={styles.meta}>{elegidos.size} de {disponibles.length}</span>
            </div>
            {[...porFuente.entries()].map(([fuente, items]) => (
              <div key={fuente} className={styles.sourceSection}>
                <div className={styles.sourceHeaderRow}>
                  <h4 className={styles.sourceHeader}>{fuente}</h4>
                  {items.length === 0 && (
                    <DosButton
                      disabled={retrying === fuente}
                      onClick={() => void reintentar(fuente)}
                      variant="ghost-small"
                    >
                      {retrying === fuente ? 'Reintentando…' : 'Reintentar'}
                    </DosButton>
                  )}
                </div>
                {items.length === 0 && retrying !== fuente ? (
                  <p className={styles.meta}>Sin resultados</p>
                ) : (
                  <div className={styles.galleryGrid}>
                    {items.map((candidato) => (
                      <label className={styles.galleryItem} key={candidato.id}>
                        <div className={styles.galleryThumb}>
                          <img
                            alt={candidato.label}
                            className={styles.previewImage}
                            src={candidato.previewUrl || candidato.url}
                          />
                        </div>
                        <div className={styles.galleryPick}>
                          <input
                            checked={elegidos.has(candidato.id)}
                            disabled={candidato.yaGuardada || guardando}
                            onChange={() => alternar(candidato.id)}
                            type="checkbox"
                          />
                          <span className={styles.name}>{candidato.label}</span>
                        </div>
                        <span className={styles.galleryBadge}>
                          {candidato.yaGuardada
                            ? 'ya guardada'
                            : candidato.delPadre
                              ? 'del romset padre'
                              : ' '}
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </>
        )}
        <div className={styles.toolbar}>
          <DosButton
            disabled={elegidos.size === 0 || guardando}
            onClick={() => void guardar()}
            variant="primary-small"
          >
            {guardando ? 'Guardando…' : `Guardar ${elegidos.size}`}
          </DosButton>
          <DosButton disabled={guardando} onClick={onClose} variant="ghost-small">Cancelar</DosButton>
        </div>
      </div>
    </Modal>
  );
}

/** Espera a que el job termine. La precarga usa polling propio; acá alcanza con esto. */
async function esperarJob(jobId: string): Promise<void> {
  for (;;) {
    const job = await getJob(jobId);
    if (job.status === 'succeeded') return;
    if (job.status === 'failed') throw new Error(job.error || 'La descarga falló.');
    if (job.status === 'cancelled') throw new Error('La descarga se canceló.');
    await new Promise((resolve) => setTimeout(resolve, 400));
  }
}
