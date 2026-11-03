import { useCallback, useEffect, useRef, useState } from 'react';
import { Card, DosButton, DosSelect, Modal, Spinner } from '@/components/dos';
import { ImageModal } from '@/components/ImageModal';
import {
  deleteGalleryImage,
  listGalleryCandidates,
  saveGallery,
  useGalleryImageAs as aplicarImagenGaleria,
  type GalleryCandidate,
  type GuardarGaleriaItem,
  type ResultadoGuardado,
} from '@/lib/api/gallery';
import { getJob } from '@/lib/api/jobs';
import { FIELDDEFS } from '@/lib/domain/types';
import type { GalleryImage, ImageKey } from '@/lib/domain/types';
import styles from './GalleryPanel.module.css';

// Se piden por separado: el buscador tarda minutos y las demás no tienen por qué esperarlo.
const TODAS_LAS_FUENTES = ['ArcadeDB', 'MyAbandonware', 'Launchbox', 'MobyGames', 'ImageSearch'];
// El buscador va de a un casillero, y de a uno por vez: cada tanda aparece cuando llega en vez
// de hacer esperar un par de minutos por todas juntas.
const CASILLEROS_DEL_BUSCADOR: ImageKey[] = ['caratula', 'captura', 'poster', 'logo', 'marquesina'];

interface GalleryPanelProps {
  gameId: string;
  gallery: GalleryImage[];
  onChanged: () => void;
  /** Solo el contenido, sin tarjeta propia: lo usa quien ya envuelve la galería en su Card numerada. */
  bare?: boolean;
}

export function GalleryPanel({ gameId, gallery, onChanged, bare = false }: GalleryPanelProps) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [error, setError] = useState('');

  const contenido = (
    <>
      <div className={styles.stack}>
        <p className={styles.meta}>
          Banco de imágenes de ArcadeDB, MyAbandonware, ImageSearch y Launchbox, aparte de los
          campos del contrato. Viaja en el paquete si tildás Galería al exportar.
        </p>
        {error ? <p className={styles.error}>{error}</p> : null}
        {gallery.length === 0 ? (
          <p className={styles.empty}>Todavía no hay imágenes en la galería.</p>
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
          <DosButton onClick={() => setPickerOpen(true)} size="sm" variant="secondary">
            Traer de todas las fuentes
          </DosButton>
        </div>
      </div>
      {pickerOpen ? (
        <GalleryPicker
          gameId={gameId}
          onClose={() => setPickerOpen(false)}
          onSaved={(resultado) => {
            setPickerOpen(false);
            setError(avisoDeFallidas(resultado));
            onChanged();
          }}
        />
      ) : null}
    </>
  );

  if (bare) return contenido;
  return <Card title="Galería">{contenido}</Card>;
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
          if (campo) void correr(() => aplicarImagenGaleria(gameId, imagen.id, campo));
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
  onSaved: (resultado: ResultadoGuardado) => void;
}) {
  const [candidatos, setCandidatos] = useState<GalleryCandidate[]>([]);
  const [buscando, setBuscando] = useState<Set<string>>(new Set());
  const [elegidos, setElegidos] = useState<Set<string>>(new Set());
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');

  // Al cerrar el modal, una búsqueda en curso deja de pedir las tandas que le faltan.
  const corrida = useRef(0);

  const cargar = useCallback(async (fuente: string, propia: number) => {
    setBuscando((previo) => new Set(previo).add(fuente));
    // La misma fuente incluye las del romset padre, que llegan con otro `source`.
    setCandidatos((previos) => previos.filter((c) => !c.source.startsWith(fuente)));
    try {
      for (const clave of fuente === 'ImageSearch' ? CASILLEROS_DEL_BUSCADOR : [undefined]) {
        const nuevos = await listGalleryCandidates(gameId, fuente, clave);
        if (corrida.current !== propia) return;
        // La misma imagen aparece en la búsqueda de más de un casillero.
        setCandidatos((previos) => {
          const vistas = new Set(previos.map((c) => c.url));
          return [...previos, ...nuevos.filter((c) => !vistas.has(c.url))];
        });
      }
    } catch (err) {
      if (corrida.current === propia) {
        setError(err instanceof Error ? err.message : 'No se pudieron traer las imágenes.');
      }
    }
    if (corrida.current !== propia) return;
    setBuscando((previo) => {
      const siguiente = new Set(previo);
      siguiente.delete(fuente);
      return siguiente;
    });
  }, [gameId]);

  useEffect(() => {
    corrida.current += 1;
    const propia = corrida.current;
    TODAS_LAS_FUENTES.forEach((fuente) => { void cargar(fuente, propia); });
    return () => { corrida.current += 1; };
  }, [cargar]);

  const reintentar = (fuente: string) => {
    setError('');
    void cargar(fuente, corrida.current);
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
  const disponibles = candidatos.filter((c) => !c.yaGuardada);
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
      onSaved(await esperarJob(jobId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudieron guardar las imágenes.');
      setGuardando(false);
    }
  }

  // Agrupar candidatos por fuente, incluyendo fuentes sin resultados
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
        {candidatos.length === 0 && buscando.size === 0 ? (
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
                  {items.length > 0 && buscando.has(fuente) && <span className={styles.meta}>Buscando más…</span>}
                  {items.length === 0 && !buscando.has(fuente) && (
                    <DosButton onClick={() => reintentar(fuente)} variant="ghost-small">Reintentar</DosButton>
                  )}
                </div>
                {items.length === 0 ? (
                  buscando.has(fuente) ? <Spinner /> : <p className={styles.meta}>Sin resultados</p>
                ) : (
                  <div className={styles.galleryGrid}>
                    {items.map((candidato) => (
                      <label
                        className={[styles.galleryItem, elegidos.has(candidato.id) ? styles.tildada : ''].filter(Boolean).join(' ')}
                        key={candidato.id}
                      >
                        <div className={styles.galleryThumb}>
                          <img
                            alt={candidato.label}
                            className={styles.previewImage}
                            loading="lazy"
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
            disabledReason={elegidos.size === 0 ? 'Elegí al menos una imagen para guardar.' : undefined}
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

/** Vacío si se bajaron todas: el guardado termina bien aunque falle alguna de las elegidas. */
function avisoDeFallidas({ guardadas, fallidas }: ResultadoGuardado): string {
  if (fallidas.length === 0) return '';
  const total = guardadas.length + fallidas.length;
  return `Se guardaron ${guardadas.length} de ${total}: ${fallidas.length === 1 ? 'la otra no se pudo bajar' : `las otras ${fallidas.length} no se pudieron bajar`} de su sitio.`;
}

/** Espera a que el job termine. La precarga usa polling propio; acá alcanza con esto. */
async function esperarJob(jobId: string): Promise<ResultadoGuardado> {
  for (;;) {
    const job = await getJob<ResultadoGuardado>(jobId);
    if (job.status === 'succeeded') return job.result ?? { guardadas: [], fallidas: [] };
    if (job.status === 'failed') throw new Error(job.error || 'La descarga falló.');
    if (job.status === 'cancelled') throw new Error('La descarga se canceló.');
    await new Promise((resolve) => setTimeout(resolve, 400));
  }
}
