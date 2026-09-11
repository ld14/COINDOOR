import { forwardRef, type ReactNode, useEffect, useImperativeHandle, useRef, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  DosButton,
  DosInput,
  DosSelect,
  DosTextarea,
  FieldTag,
  Panel,
  ProgressBar,
  SectionHeader,
  Spinner,
  StatusBadge,
  SunkenBox,
} from '@/components/dos';
import { SuggestionsModal } from '@/components/SuggestionsModal';
import { IdentityBatchModal } from '@/components/IdentityBatchModal';
import { ImageModal } from '@/components/ImageModal';
import { GalleryPanel } from '@/components/GalleryPanel';
import { YoutubeDownload } from '@/components/YoutubeDownload';
import { useGame } from '@/hooks/useGame';
import { useGameMutations } from '@/hooks/useGameMutations';
import { useSystems } from '@/hooks/useSystems';
import { useDominantColors } from '@/hooks/useDominantColors';
import { soportaArcadeDb, soportaMsdos } from '@/lib/domain/arcade';
import { computeGameStatus, missingRequired } from '@/lib/domain/completeness';
import { FIELDDEFS } from '@/lib/domain/types';
import type {
  CheatGroup,
  Game,
  Identity,
  IdentityKey,
  ImageKey,
  MediaField,
  ReviewCat,
  System,
  TextKey,
  Tratamiento,
  VideoKey,
} from '@/lib/domain/types';
import { parseCheatsText } from '@/lib/api/fields';
import { searchManuals, type ManualSearchResult } from '@/lib/api/manuals';
import { searchMagazines, setMagazine, addAppearance, removeAppearance, buildMagazineLinks, type MagazineSearchResult } from '@/lib/api/magazines';
import { getJob, type JobStatus } from '@/lib/api/jobs';
import { startPrecarga, startPrecargaMsdos } from '@/lib/api/games';
import styles from './ReadPages.module.css';

const MANUAL_DELETE_CONFIRM = 'Este campo fue cargado a mano. ¿Borrarlo de todas formas?';

type SaveHandle = { save: () => void };
/** 0 = acento primario, 1 = secundario. */
type AccentSlot = 0 | 1;
type PresentationHandle = SaveHandle & { setAccent: (slot: AccentSlot, value: string) => void };

function confirmManualDelete(status: string, action: () => void) {
  if (status === 'manual' && !window.confirm(MANUAL_DELETE_CONFIRM)) return;
  action();
}


const SUGGESTABLE_LABELS: Record<string, string> = {
  ...Object.fromEntries(FIELDDEFS.identity.map((field) => [field.key, field.label])),
  ...Object.fromEntries(FIELDDEFS.images.map((field) => [field.key, field.label])),
  sinopsis: 'Sinopsis',
  review: 'Reseña',
  cheats: 'Trucos',
  video: 'Video de gameplay',
};

function isIdentityKey(key: string): key is IdentityKey {
  return FIELDDEFS.identity.some((field) => field.key === key);
}

interface SuggestionCurrent {
  hasContent: boolean;
  isManual: boolean;
  previewUrl?: string | null;
  value?: string | null;
}

function suggestionStatus(game: Game, key: string): SuggestionCurrent {
  if (isIdentityKey(key)) {
    const value = game.identity[key];
    return { hasContent: value !== '', isManual: game.identitySource === 'manual', value };
  }
  if (FIELDDEFS.images.some((f) => f.key === key)) {
    const img = game.images[key as ImageKey];
    return { hasContent: img?.status !== 'empty', isManual: img?.status === 'manual', previewUrl: img?.url };
  }
  if (key === 'sinopsis') {
    const t = game.texts.sinopsis;
    return { hasContent: t.value !== '', isManual: t.status === 'manual', value: t.value };
  }
  if (key === 'review') {
    return { hasContent: game.review.status !== 'empty', isManual: game.review.status === 'manual' };
  }
  if (key === 'cheats') {
    const c = game.cheats;
    const value = c.groups.length > 0 ? JSON.stringify({ groups: c.groups.map(g => ({ name: g.name, entries: g.entries })) }) : '';
    return { hasContent: c.status !== 'empty', isManual: c.status === 'manual', value };
  }
  const v = game.video.video;
  return { hasContent: v.status !== 'empty', isManual: v.status === 'manual', previewUrl: v.url };
}

export function FichaJuego() {
  const { gameId = '' } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const precargaJobId = searchParams.get('precarga');
  const navigate = useNavigate();
  const { data: game, error, isLoading, refetch: refetchGame } = useGame(gameId);
  const mutations = useGameMutations(gameId);
  const { data: systems = [] } = useSystems();
  const [missingAfterReady, setMissingAfterReady] = useState<string[]>([]);
  const [suggestField, setSuggestField] = useState<string | null>(null);
  const [suggestIdentityBatch, setSuggestIdentityBatch] = useState(false);
  const [precargaLoading, setPrecargaLoading] = useState(false);
  const sectionRefs = useRef<Record<string, SaveHandle | null>>({});
  const presentationRef = useRef<PresentationHandle | null>(null);
  const [proximoAcento, setProximoAcento] = useState<AccentSlot>(0);

  const saveAll = () => {
    for (const ref of Object.values(sectionRefs.current)) ref?.save();
  };

  // Cada clic en un color predominante alterna: primero el acento primario,
  // después el secundario. Queda cargado en Presentación, no guardado — se
  // persiste con "Guardar presentación" o "Guardar todo", como el resto.
  const aplicarColorDominante = (hex: string) => {
    presentationRef.current?.setAccent(proximoAcento, hex);
    setProximoAcento((slot) => (slot === 0 ? 1 : 0));
  };

  if (isLoading) return <p className={styles.meta}>Cargando ficha…</p>;
  if (error || !game) {
    return (
      <div className={styles.page}>
        <Link className={styles.backLink} to="/juegos">&lt;&lt; Juegos</Link>
        <Panel>
          <SectionHeader>Error</SectionHeader>
          <SunkenBox><p className={styles.error}>Juego no encontrado.</p></SunkenBox>
        </Panel>
      </div>
    );
  }

  const isArcade = soportaArcadeDb(game.systemId);
  const isMsdos = soportaMsdos(game.systemId);

  const handlePrecarga = async () => {
    setPrecargaLoading(true);
    try {
      const result = isMsdos
        ? await startPrecargaMsdos(game.id)
        : await startPrecarga(game.id);
      setSearchParams({ precarga: result.jobId });
    } catch {
      // Error silenciado: el usuario puede reintentar.
    } finally {
      setPrecargaLoading(false);
    }
  };

  const missing = missingRequired(game);
  const status = computeGameStatus(game);

  return (
    <div className={styles.page}>
      {precargaJobId ? (
        <PrecargaBanner
          jobId={precargaJobId}
          onComplete={() => {
            setSearchParams({});
            void refetchGame();
          }}
        />
      ) : null}
      {isArcade && !precargaJobId ? (
        <Panel>
          <SectionHeader>PRECARGA DE ARCADEDB</SectionHeader>
          <SunkenBox className={styles.stack}>
            <p className={styles.meta}>Buscar datos del juego en Arcade Database (identidad, imágenes, sinopsis, trucos, gabinete).</p>
            <div className={styles.toolbar}>
              <DosButton disabled={precargaLoading} onClick={handlePrecarga} variant="primary-small">
                {precargaLoading ? 'Iniciando…' : 'Precargar ArcadeDB'}
              </DosButton>
            </div>
          </SunkenBox>
        </Panel>
      ) : null}
      {isMsdos && !precargaJobId ? (
        <Panel>
          <SectionHeader>PRECARGA DE MSDOS</SectionHeader>
          <SunkenBox className={styles.stack}>
            <p className={styles.meta}>Buscar datos del juego en Launchbox + IA (año, imágenes, identidad, sinopsis).</p>
            <div className={styles.toolbar}>
              <DosButton disabled={precargaLoading} onClick={handlePrecarga} variant="primary-small">
                {precargaLoading ? 'Iniciando…' : 'Precargar Launchbox + IA'}
              </DosButton>
            </div>
          </SunkenBox>
        </Panel>
      ) : null}
      <GameHero
        game={game}
        systems={systems}
        missing={missing}
        onSaveAll={saveAll}
        onSystemChange={(systemId) => mutations.patchGame.mutate({ systemId })}
        onMarkReady={() => {
          setMissingAfterReady(missing);
          if (missing.length === 0) void mutations.markReady.mutateAsync();
        }}
        onSaveTratamiento={(tratamiento) => mutations.patchGame.mutate({ tratamiento })}
        onSaveRomRef={(romRef) => mutations.patchGame.mutate({ romRef })}
        onUploadRom={(file) => mutations.uploadRom.mutate(file)}
        onExport={() => { saveAll(); navigate(`/exportar/${game.id}`); }}
        onPickColor={aplicarColorDominante}
        proximoAcento={proximoAcento}
        status={status}
      />

      {mutations.patchGame.error ? (
        <Panel>
          <SectionHeader>NO SE GUARDÓ EL CAMBIO:</SectionHeader>
          <SunkenBox>
            <p className={styles.error}>{mutations.patchGame.error.message}</p>
          </SunkenBox>
        </Panel>
      ) : null}

      <CompletionDashboard game={game} missing={missing} />

      {missingAfterReady.length > 0 ? (
        <Panel>
          <SectionHeader>NO SE PUEDE MARCAR COMO LISTO — faltan campos requeridos:</SectionHeader>
          <SunkenBox>
            {missingAfterReady.map((item) => <p className={styles.error} key={item}>- {item}</p>)}
          </SunkenBox>
        </Panel>
      ) : null}

      {game.errors.length > 0 ? (
        <Panel>
          <SectionHeader>ERRORES DE FORMATO (bloquean el export):</SectionHeader>
          <SunkenBox>
            {game.errors.map((item) => (
              <p className={styles.error} key={`${item.field}-${item.message}`}>
                - {item.field} — {item.message}
              </p>
            ))}
          </SunkenBox>
        </Panel>
      ) : null}

      <div className={styles.sections}>
        <IdentitySection ref={(r) => { sectionRefs.current.identity = r; }} game={game} onSave={(identity) => mutations.patchGame.mutate({ identity })} onSuggest={setSuggestField} onSuggestBatch={() => setSuggestIdentityBatch(true)} />
        <MediaSection
          game={game}
          onDelete={(key) => mutations.deleteField.mutate(key)}
          onSuggestVideo={() => setSuggestField('video')}
          onSuggestImage={(key) => setSuggestField(key)}
          onUpload={(key, file) => mutations.uploadMedia.mutate({ key, file })}
          onGalleryChanged={() => void refetchGame()}
        />
        <TextSection
          ref={(r) => { sectionRefs.current.texts = r; }}
          game={game}
          onDelete={(key) => mutations.deleteField.mutate(key)}
          onSuggest={() => setSuggestField('sinopsis')}
          onText={(key, value) => mutations.setTextField.mutate({ key, value })}
        />
        <ReviewSection
          ref={(r) => { sectionRefs.current.review = r; }}
          game={game}
          onReview={(score, cats) => mutations.setReview.mutate({ score, cats })}
          onSuggest={() => setSuggestField('review')}
        />
        <CheatsSection
          ref={(r) => { sectionRefs.current.cheats = r; }}
          game={game}
          onCheats={(groups) => mutations.setCheats.mutate({ groups })}
          onDelete={() => mutations.deleteField.mutate('cheats')}
          onSuggest={() => setSuggestField('cheats')}
        />
        <PresentationSection
          ref={(r) => { sectionRefs.current.presentation = r; presentationRef.current = r; }}
          game={game}
          onSave={(accentValue, accent2Value) => mutations.patchGame.mutate({
            accent: accentValue ? 'manual' : 'empty',
            accentValue,
            accent2Value,
          })}
        />
        <ManualSection game={game} onUpload={(file) => mutations.uploadManual.mutate(file)} onDelete={(id) => mutations.deleteManual.mutate(id)} />
        <MagazineSection game={game} />
        <CabinetSection game={game} />
      </div>

      {suggestField ? (
        <SuggestionsModal
          fieldKey={suggestField}
          gameId={game.id}
          hasContent={suggestionStatus(game, suggestField).hasContent}
          isManual={suggestionStatus(game, suggestField).isManual}
          label={SUGGESTABLE_LABELS[suggestField]}
          onApply={(candidateId) => mutations.applySuggestion.mutate({ key: suggestField, candidateId })}
          onClose={() => setSuggestField(null)}
          open
          current={{ previewUrl: suggestionStatus(game, suggestField).previewUrl, value: suggestionStatus(game, suggestField).value }}
        />
      ) : null}

      {suggestIdentityBatch ? (
        <IdentityBatchModal
          gameId={game.id}
          open={suggestIdentityBatch}
          onClose={() => setSuggestIdentityBatch(false)}
          onApplied={() => void refetchGame()}
        />
      ) : null}
    </div>
  );
}

function GameHero({ game, systems, missing, onSaveAll, onSystemChange, onMarkReady, onSaveTratamiento, onSaveRomRef, onUploadRom, onExport, onPickColor, proximoAcento, status }: { game: Game; systems: System[]; missing: string[]; onSaveAll: () => void; onSystemChange: (systemId: string) => void; onMarkReady: () => void; onSaveTratamiento: (tratamiento: string) => void; onSaveRomRef: (romRef: string) => void; onUploadRom: (file: File) => void; onExport: () => void; onPickColor: (hex: string) => void; proximoAcento: AccentSlot; status: ReturnType<typeof computeGameStatus> }) {
  const coverUrl = game.images.caratula?.url;
  const heroMedia = coverUrl ?? game.video.video?.url;
  const { colors } = useDominantColors(coverUrl, 4);
  const [tratamiento, setTratamiento] = useState(game.tratamiento || 'copiar');
  const [romPath, setRomPath] = useState(game.romRef || '');
  const [romFile, setRomFile] = useState<File | null>(null);

  const romFileName = romFile?.name || (game.romRef ? game.romRef.split('/').pop() || game.romRef : '');

  const handleSaveTratamiento = () => {
    onSaveTratamiento(tratamiento);
    if (romFile) {
      onUploadRom(romFile);
    } else if (romPath !== game.romRef) {
      onSaveRomRef(romPath);
    }
  };

  return (
    <div className={styles.gameHero}>
      <div className={styles.heroPreview}>
        {heroMedia ? <img alt={game.identity.title} className={styles.previewImage} src={heroMedia} /> : `${game.identity.title} · carátula pendiente`}
      </div>
      <div className={styles.heroRight}>
        <Link className={styles.backLink} to="/juegos">&lt;&lt; Juegos</Link>
        <h1 className={styles.title}>{game.identity.title}</h1>
        <Panel className={styles.heroPanel}>
          <SunkenBox className={styles.heroFields}>
            <DosSelect
              aria-label="Plataforma"
              className={styles.systemSelect}
              value={game.systemId}
              onChange={(e) => onSystemChange(e.target.value)}
            >
              {systems.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </DosSelect>
            <StatusBadge status={status} />
            {colors.length > 0 ? (
              <div className={styles.colorPalette}>
                <span className={styles.paletteLabel}>
                  Colores predominantes
                  <span className={styles.paletteHint}> — clic: acento {proximoAcento === 0 ? 'primario' : 'secundario'}</span>
                </span>
                <div className={styles.swatches}>
                  {colors.map((color) => (
                    <button
                      aria-label={`Usar ${color.hex} como acento ${proximoAcento === 0 ? 'primario' : 'secundario'}`}
                      className={styles.colorSwatch}
                      key={color.hex}
                      onClick={() => onPickColor(color.hex)}
                      type="button"
                    >
                      <span className={styles.colorBlock} style={{ backgroundColor: color.hex }} />
                      <span className={styles.colorHex}>{color.hex}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
            <div className={styles.tratamientoField}>
              <span className={styles.label}>Tratamiento</span>
              <div className={styles.tratamientoRow}>
                <DosSelect aria-label="Tratamiento" className={styles.tratamientoSelect} value={tratamiento} onChange={(e) => setTratamiento(e.target.value as Tratamiento)}>
                  <option value="copiar">Copiar (romset)</option>
                  <option value="descomprimir">Descomprimir (archivos sueltos)</option>
                </DosSelect>
              </div>
            </div>
            <div className={styles.tratamientoField}>
              <span className={styles.label}>Archivo del juego</span>
              {romFileName ? (
                <div className={styles.romInfo}>
                  <span className={styles.romName}>{romFileName}</span>
                </div>
              ) : (
                <span className={styles.empty}>No adjunto</span>
              )}
              <div className={styles.tratamientoRow}>
                <label className={styles.romUpload}>
                  <input
                    type="file"
                    accept=".zip,.nes,.sms,.gb,.gbc,.gba,.gen,.smc,.sfc,.pce,.ngp,.ngpc,.col,.sg"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) setRomFile(file);
                    }}
                  />
                  <span className={styles.romUploadBtn}>Adjuntar archivo</span>
                </label>
              </div>
              <div className={styles.tratamientoRow}>
                <DosInput
                  aria-label="Path del ROM"
                  className={styles.romPathInput}
                  placeholder="O ingresar path del archivo..."
                  value={romPath}
                  onChange={(e) => setRomPath(e.target.value)}
                />
              </div>
            </div>
          </SunkenBox>
          <div className={styles.heroToolbar}>
            <DosButton onClick={handleSaveTratamiento} variant="primary-small">Guardar</DosButton>
            <DosButton onClick={onSaveAll} variant="ghost-small">Guardar todo</DosButton>
            <DosButton onClick={onMarkReady} variant="ghost-small">Marcar como listo</DosButton>
          </div>
          {status === 'ready' ? (
            <div className={styles.heroToolbar}>
              <DosButton onClick={onExport} variant="ghost-small" className={styles.heroExport}>Exportar</DosButton>
            </div>
          ) : null}
        </Panel>
      </div>
    </div>
  );
}

function CompletionDashboard({ game, missing }: { game: Game; missing: string[] }) {
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

const IdentitySection = forwardRef<SaveHandle, { game: Game; onSave: (identity: Identity) => void; onSuggest: (key: IdentityKey) => void; onSuggestBatch: () => void }>(function IdentitySection({ game, onSave, onSuggest, onSuggestBatch }, ref) {
  const [identity, setIdentity] = useState(game.identity);
  useEffect(() => setIdentity(game.identity), [game.identity]);
  useImperativeHandle(ref, () => ({ save: () => onSave(identity) }), [onSave, identity]);
  return (
    <Panel>
      <SectionHeader>IDENTIDAD</SectionHeader>
      <SunkenBox className={styles.fields}>
        {FIELDDEFS.identity.map((field) => (
          <label className={styles.field} key={field.key}>
            <span className={styles.label}>{field.label}</span>
            <DosInput
              aria-label={field.label}
              onChange={(event) => setIdentity({ ...identity, [field.key]: event.target.value })}
              value={identity[field.key]}
            />
            <DosButton onClick={() => onSuggest(field.key)} type="button" variant="ghost-small">Sugerir</DosButton>
          </label>
        ))}
      </SunkenBox>
      <div className={styles.toolbar}>
        <span className={styles.meta}>Fuente actual: {game.identitySource}</span>
        <DosButton onClick={onSuggestBatch} variant="ghost-small">Sugerir todo</DosButton>
        <DosButton onClick={() => onSave(identity)} variant="primary-small">Guardar identidad</DosButton>
      </div>
    </Panel>
  );
});

function MediaSection({
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

const TextSection = forwardRef<SaveHandle, {
  game: Game;
  onDelete: (key: string) => void;
  onSuggest: () => void;
  onText: (key: TextKey, value: string) => void;
}>(function TextSection({ game, onDelete, onSuggest, onText }, ref) {
  const [sinopsis, setSinopsis] = useState(game.texts.sinopsis.value);
  useEffect(() => setSinopsis(game.texts.sinopsis.value), [game.texts.sinopsis.value]);
  useImperativeHandle(ref, () => ({ save: () => onText('sinopsis', sinopsis) }), [onText, sinopsis]);

  return (
    <Panel>
      <SectionHeader>TEXTOS</SectionHeader>
      <SunkenBox>
        <div className={styles.fieldTop}><span className={styles.name}>Sinopsis</span><FieldTag status={game.texts.sinopsis.status} /></div>
        <DosTextarea aria-label="Sinopsis" maxLength={FIELDDEFS.texts[0].maxLength} onChange={(event) => setSinopsis(event.target.value)} value={sinopsis} />
        <div className={styles.toolbar}>
          <DosButton onClick={() => onText('sinopsis', sinopsis)} variant="primary-small">Guardar sinopsis</DosButton>
          <DosButton onClick={onSuggest} variant="ghost-small">Sugerir</DosButton>
          <DosButton onClick={() => confirmManualDelete(game.texts.sinopsis.status, () => onDelete('sinopsis'))} variant="danger-small">Borrar</DosButton>
        </div>
      </SunkenBox>
    </Panel>
  );
});

const ReviewSection = forwardRef<SaveHandle, { game: Game; onReview: (score: number | null, cats: Partial<Record<ReviewCat, number>>) => void; onSuggest: () => void }>(function ReviewSection({ game, onReview, onSuggest }, ref) {
  const [reviewScore, setReviewScore] = useState(String(game.review.score ?? ''));
  useEffect(() => setReviewScore(String(game.review.score ?? '')), [game.review.score]);
  useImperativeHandle(ref, () => ({ save: () => onReview(reviewScore ? Number(reviewScore) : null, game.review.cats) }), [onReview, reviewScore, game.review.cats]);
  return (
    <Panel>
      <SectionHeader>RESEÑA</SectionHeader>
      <SunkenBox className={styles.stack}>
        <div className={styles.fieldTop}><span className={styles.name}>Puntaje y categorías</span><FieldTag status={game.review.status} /></div>
        <div className={styles.reviewGrid}>
          <label className={styles.field}>
            <span className={styles.label}>Puntaje</span>
            <DosInput aria-label="Puntaje de reseña" onChange={(event) => setReviewScore(event.target.value)} placeholder="0-100" value={reviewScore} />
          </label>
          <div className={styles.scorePlate}>{reviewScore || '--'}</div>
        </div>
        <div className={styles.catGrid}>
          {Object.entries(game.review.cats).length ? Object.entries(game.review.cats).map(([cat, score]) => (
            <span className={styles.catPill} key={cat}>{cat}: {score}</span>
          )) : <span className={styles.empty}>Sin Información</span>}
        </div>
        <div className={styles.toolbar}>
          <DosButton onClick={() => onReview(reviewScore ? Number(reviewScore) : null, game.review.cats)} variant="primary-small">Guardar reseña</DosButton>
          <DosButton onClick={onSuggest} variant="ghost-small">Sugerir</DosButton>
        </div>
      </SunkenBox>
    </Panel>
  );
});

const CheatsSection = forwardRef<SaveHandle, {
  game: Game;
  onCheats: (groups: CheatGroup[]) => void;
  onDelete: () => void;
  onSuggest: () => void;
}>(function CheatsSection({ game, onCheats, onDelete, onSuggest }, ref) {
  const [groups, setGroups] = useState<CheatGroup[]>(game.cheats.groups);
  const [editando, setEditando] = useState(false);
  // Mientras se edita, lo que llega del servidor no pisa lo que el usuario escribió.
  useEffect(() => {
    if (!editando) setGroups(game.cheats.groups);
  }, [editando, game.cheats.groups]);
  useImperativeHandle(ref, () => ({ save: () => onCheats(groups) }), [onCheats, groups]);

  const draftKey = `coindoor:cheats-draft:${game.id}`;
  const [pastedText, setPastedText] = useState(() => {
    try {
      return localStorage.getItem(draftKey) ?? '';
    } catch {
      return '';
    }
  });
  const [interpreting, setInterpreting] = useState(false);
  const [interpretError, setInterpretError] = useState<string | null>(null);

  useEffect(() => {
    try {
      if (pastedText) {
        localStorage.setItem(draftKey, pastedText);
      } else {
        localStorage.removeItem(draftKey);
      }
    } catch {
      // localStorage no disponible (privado, cuota, etc.): el borrador solo vive en memoria.
    }
  }, [draftKey, pastedText]);

  const handleInterpret = async () => {
    if (!pastedText.trim()) return;
    setInterpreting(true);
    setInterpretError(null);
    try {
      const result = await parseCheatsText(game.id, pastedText);
      if (result.groups.length === 0) {
        setInterpretError('No se encontró ningún truco identificable en ese texto.');
      } else {
        setGroups((prev) => [...prev, ...result.groups]);
      }
    } catch (err) {
      setInterpretError(err instanceof Error ? err.message : 'No se pudo interpretar el texto.');
    } finally {
      setInterpreting(false);
    }
  };

  const updateGroupName = (groupIdx: number, name: string) => {
    setGroups((prev) => prev.map((g, i) => (i === groupIdx ? { ...g, name } : g)));
  };
  const removeGroup = (groupIdx: number) => {
    setGroups((prev) => prev.filter((_, i) => i !== groupIdx));
  };
  const addGroup = () => {
    setGroups((prev) => [...prev, { name: 'Nuevo grupo', entries: [] }]);
  };
  const updateEntry = (groupIdx: number, entryIdx: number, field: keyof CheatGroup['entries'][number], value: string) => {
    setGroups((prev) => prev.map((g, i) => (
      i === groupIdx
        ? { ...g, entries: g.entries.map((e, j) => (j === entryIdx ? { ...e, [field]: value } : e)) }
        : g
    )));
  };
  const removeEntry = (groupIdx: number, entryIdx: number) => {
    setGroups((prev) => prev.map((g, i) => (
      i === groupIdx ? { ...g, entries: g.entries.filter((_, j) => j !== entryIdx) } : g
    )));
  };
  const addEntry = (groupIdx: number) => {
    setGroups((prev) => prev.map((g, i) => (
      i === groupIdx ? { ...g, entries: [...g.entries, { name: '', input: '' }] } : g
    )));
  };

  return (
    <Panel>
      <SectionHeader>TRUCOS</SectionHeader>
      <SunkenBox className={styles.stack}>
        <div className={styles.fieldTop}><span className={styles.name}>Códigos cargados</span><FieldTag status={game.cheats.status} /></div>
        {!editando && groups.length > 0 ? (
          <div className={styles.cheatLedger}>
            {groups.map((group, groupIdx) => (
              <div className={styles.cheatGroup} key={groupIdx}>
                <span className={styles.cheatGroupName}>{group.name}</span>
                {group.entries.map((entry, entryIdx) => (
                  <div className={styles.cheatEntry} key={entryIdx}>
                    <span>{entry.name}</span>
                    <code>{entry.input}</code>
                  </div>
                ))}
              </div>
            ))}
          </div>
        ) : null}
        {editando && groups.length > 0 ? (
          <div className={styles.cheatLedger}>
            {groups.map((group, groupIdx) => (
              <div className={styles.cheatGroup} key={groupIdx}>
                <div className={styles.cheatGroupEdit}>
                  <DosInput aria-label="Nombre del grupo" onChange={(event) => updateGroupName(groupIdx, event.target.value)} value={group.name} />
                  <DosButton onClick={() => removeGroup(groupIdx)} variant="danger-small">Eliminar grupo</DosButton>
                </div>
                {group.entries.map((entry, entryIdx) => (
                  <div className={styles.cheatEntryEdit} key={entryIdx}>
                    <DosInput aria-label="Qué hace el truco" onChange={(event) => updateEntry(groupIdx, entryIdx, 'name', event.target.value)} placeholder="Qué hace" value={entry.name} />
                    <DosInput aria-label="Código o procedimiento" onChange={(event) => updateEntry(groupIdx, entryIdx, 'input', event.target.value)} placeholder="Código / procedimiento" value={entry.input} />
                    <DosButton onClick={() => removeEntry(groupIdx, entryIdx)} variant="danger-small">Eliminar</DosButton>
                  </div>
                ))}
                <div className={styles.toolbar}>
                  <DosButton onClick={() => addEntry(groupIdx)} variant="ghost-small">+ Agregar truco</DosButton>
                </div>
              </div>
            ))}
          </div>
        ) : null}
        {groups.length === 0 ? <p className={styles.empty}>No Disponible</p> : null}
        {editando ? (
          <div className={styles.toolbar}>
            <DosButton onClick={addGroup} variant="ghost-small">+ Agregar grupo</DosButton>
            <DosButton onClick={() => { onCheats(groups); setEditando(false); }} variant="primary-small">Guardar trucos</DosButton>
            <DosButton onClick={() => { setGroups(game.cheats.groups); setEditando(false); }} variant="ghost-small">Cancelar</DosButton>
          </div>
        ) : (
          <div className={styles.toolbar}>
            <DosButton onClick={() => setEditando(true)} variant="primary-small">Editar trucos</DosButton>
            <DosButton onClick={onSuggest} variant="ghost-small">Sugerir</DosButton>
            <DosButton onClick={() => confirmManualDelete(game.cheats.status, onDelete)} variant="danger-small">Borrar</DosButton>
          </div>
        )}
        {editando ? (
          <div className={styles.field}>
            <span className={styles.label}>Pegar texto (Markdown, lista o prosa)</span>
            <DosTextarea
              aria-label="Texto de trucos a interpretar"
              onChange={(event) => setPastedText(event.target.value)}
              placeholder="Pegá acá una guía, lista o texto suelto con trucos…"
              value={pastedText}
            />
            <div className={styles.toolbar}>
              <DosButton disabled={interpreting || !pastedText.trim()} onClick={() => void handleInterpret()} variant="ghost-small">
                {interpreting ? 'Interpretando…' : 'Interpretar con IA'}
              </DosButton>
              {interpreting ? <Spinner /> : null}
            </div>
            {interpretError ? <p className={styles.error}>{interpretError}</p> : null}
          </div>
        ) : null}
      </SunkenBox>
    </Panel>
  );
});

const hex = (value: string) => `#${value}`;

const ACCENT_PRESETS = [
  { label: 'dorado', value: hex('d4a017'), className: styles.swatchGold },
  { label: 'cian', value: hex('00aaaa'), className: styles.swatchCyan },
  { label: 'rojo', value: hex('aa0000'), className: styles.swatchRed },
  { label: 'verde', value: hex('006600'), className: styles.swatchGreen },
  { label: 'azul', value: hex('0000aa'), className: styles.swatchBlue },
];

const PresentationSection = forwardRef<PresentationHandle, {
  game: Game;
  onSave: (accentValue: string, accent2Value: string) => void;
}>(function PresentationSection({ game, onSave }, ref) {
  const [accentValue, setAccentValue] = useState(game.accentValue);
  const [accent2Value, setAccent2Value] = useState(game.accent2Value);
  useEffect(() => setAccentValue(game.accentValue), [game.accentValue]);
  useEffect(() => setAccent2Value(game.accent2Value), [game.accent2Value]);
  useImperativeHandle(ref, () => ({
    save: () => onSave(accentValue, accent2Value),
    // Los colores predominantes de la carátula viven en el encabezado, que es
    // otro componente: entran por acá en vez de subir el estado de acento a la
    // página entera.
    setAccent: (slot: AccentSlot, value: string) => {
      if (slot === 0) setAccentValue(value);
      else setAccent2Value(value);
    },
  }), [onSave, accentValue, accent2Value]);
  return (
    <Panel>
      <SectionHeader>PRESENTACIÓN</SectionHeader>
      <SunkenBox className={styles.accentPanel}>
        <AccentRow label="Color de acento primario" status={game.accent} value={accentValue} onChange={setAccentValue} />
        <AccentRow label="Color de acento secundario" status={accent2Value ? game.accent : 'empty'} value={accent2Value} onChange={setAccent2Value} />
        <div className={styles.accentActions}>
          <DosButton onClick={() => onSave(accentValue, accent2Value)} variant="primary-small">Guardar presentación</DosButton>
        </div>
      </SunkenBox>
    </Panel>
  );
});

function AccentRow({ label, onChange, status, value }: { label: string; onChange: (value: string) => void; status: string; value: string }) {
  return (
    <div className={styles.accentRow}>
      <div className={styles.accentTopline}>
        <span className={styles.name}>{label}</span>
        <span className={styles.meta}>{status === 'empty' ? 'sin definir' : status === 'suggested' ? 'sugerido' : 'cargado'}</span>
      </div>
      <div className={styles.swatches}>
        {ACCENT_PRESETS.map((preset) => (
          <button
            aria-label={`${label} ${preset.label}`}
            className={[styles.swatch, preset.className, value.toLowerCase() === preset.value ? styles.swatchActive : ''].filter(Boolean).join(' ')}
            key={preset.label}
            onClick={() => onChange(preset.value)}
            type="button"
          />
        ))}
      </div>
      <label className={styles.hexField}>
        <span className={styles.label}>Agregar color HEX:</span>
        <DosInput aria-label={label} onChange={(event) => onChange(event.target.value)} placeholder="#RRGGBB" value={value} />
      </label>
    </div>
  );
}

function ManualSection({ game, onUpload, onDelete }: { game: Game; onUpload: (file: File) => void; onDelete: (id: string) => void }) {
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<ManualSearchResult[]>([]);

  const handleSearch = async () => {
    setSearching(true);
    setResults([]);
    try {
      const data = await searchManuals(game.id);
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <Panel>
      <SectionHeader>MANUAL</SectionHeader>
      <SunkenBox className={styles.stack}>
        {game.manuals.length > 0 ? (
          <div className={styles.cheatLedger}>
            {game.manuals.map((manual) => (
              <div className={styles.cheatEntry} key={manual.id}>
                <span>📎 {manual.fileName}</span>
                <span className={styles.meta}>{manual.status} — {manual.pages} páginas</span>
                <DosButton onClick={() => onDelete(manual.id)} variant="danger-small">Borrar</DosButton>
              </div>
            ))}
          </div>
        ) : <p className={styles.empty}>No Disponible</p>}
        <div className={styles.toolbar}>
          <label className={styles.meta}>
            Cargar PDF:
            <input
              multiple
              accept=".pdf"
              onChange={(event) => {
                const files = event.target.files;
                if (files) Array.from(files).forEach((file) => onUpload(file));
              }}
              type="file"
            />
          </label>
          <DosButton disabled={searching} onClick={handleSearch} variant="ghost-small">
            {searching ? 'Buscando…' : 'Buscar manuales'}
          </DosButton>
        </div>
        {searching ? (
          <div className={styles.toolbar}>
            <Spinner />
            <span className={styles.meta}>Buscando manuales digitales…</span>
          </div>
        ) : null}
        {results.length > 0 ? (
          <div className={styles.stack}>
            <span className={styles.name}>Resultados de búsqueda:</span>
            {results.map((result) => (
              <div className={styles.cheatEntry} key={result.url}>
                <span>{result.title}</span>
                <span className={styles.meta}>{result.source}</span>
                <DosButton onClick={() => window.open(result.url, '_blank')} variant="ghost-small">Abrir</DosButton>
              </div>
            ))}
          </div>
        ) : null}
      </SunkenBox>
    </Panel>
  );
}

function MagazineSection({ game }: { game: Game }) {
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<MagazineSearchResult[]>([]);

  const handleSearch = async () => {
    setSearching(true);
    setResults([]);
    try {
      const data = await searchMagazines(game.id);
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleAddAppearance = async (result: MagazineSearchResult) => {
    if (!result.appearance) return;
    await addAppearance(game.id, result.appearance);
    window.location.reload();
  };

  const handleRemoveAppearance = async (appearanceId: string) => {
    await removeAppearance(game.id, appearanceId);
    window.location.reload();
  };

  const appearances = game.magazineAppearances || [];

  return (
    <Panel>
      <SectionHeader>REVISTA</SectionHeader>
      <SunkenBox className={styles.stack}>
        {game.magazine === 'linked' ? (
          <div className={styles.cheatEntry}>
            <span className={styles.name}>{game.magazineName}</span>
            <DosButton onClick={() => { setMagazine(game.id, ''); window.location.reload(); }} variant="danger-small">Desvincular</DosButton>
          </div>
        ) : null}
        {appearances.length > 0 ? (
          <div className={styles.stack}>
            <span className={styles.name}>Apariciones en revistas:</span>
            {appearances.map((a) => {
              const links = buildMagazineLinks(a);
              return (
                <div className={styles.cheatEntry} key={a.id}>
                  <span className={styles.name}>{a.magazineName}</span>
                  {a.issueNumber ? <span className={styles.meta}>N° {a.issueNumber}</span> : null}
                  {a.date ? <span className={styles.meta}>{a.date}</span> : null}
                  <span className={styles.meta}>{a.contentType}</span>
                  <span className={styles.meta}>{a.appearanceType}</span>
                  {links.archiveOrg ? (
                    <DosButton onClick={() => window.open(links.archiveOrg, '_blank')} variant="ghost-small">Archive.org</DosButton>
                  ) : null}
                  {links.retroCdn ? (
                    <DosButton onClick={() => window.open(links.retroCdn, '_blank')} variant="ghost-small">Retro CDN</DosButton>
                  ) : null}
                  <DosButton onClick={() => handleRemoveAppearance(a.id)} variant="danger-small">Eliminar</DosButton>
                </div>
              );
            })}
          </div>
        ) : <p className={styles.empty}>Sin cobertura en revistas</p>}
        <div className={styles.toolbar}>
          <DosButton disabled={searching} onClick={handleSearch} variant="ghost-small">
            {searching ? 'Buscando…' : 'Buscar revistas'}
          </DosButton>
        </div>
        {searching ? (
          <div className={styles.toolbar}>
            <Spinner />
            <span className={styles.meta}>Identificando apariciones en revistas…</span>
          </div>
        ) : null}
        {results.length > 0 ? (
          <div className={styles.stack}>
            <span className={styles.name}>Resultados:</span>
            {results.map((result, idx) => (
              <div className={styles.cheatEntry} key={result.url || idx}>
                <span>{result.title}</span>
                <span className={styles.meta}>{result.magazine}</span>
                {result.url ? (
                  <DosButton onClick={() => window.open(result.url, '_blank')} variant="ghost-small">Abrir</DosButton>
                ) : null}
                {result.links?.archiveOrg ? (
                  <DosButton onClick={() => window.open(result.links!.archiveOrg, '_blank')} variant="ghost-small">Archive.org</DosButton>
                ) : null}
                {result.links?.retroCdn ? (
                  <DosButton onClick={() => window.open(result.links!.retroCdn, '_blank')} variant="ghost-small">Retro CDN</DosButton>
                ) : null}
                {result.appearance ? (
                  <DosButton onClick={() => handleAddAppearance(result)} variant="ghost-small">Agregar</DosButton>
                ) : null}
              </div>
            ))}
          </div>
        ) : null}
      </SunkenBox>
    </Panel>
  );
}

function summary(game: Game, missing: string[]) {
  if (game.errors.length) return `${game.errors.length} error(es) de formato`;
  if (missing.length) return `${missing.length} campo(s) faltante(s)`;
  return 'Completo';
}

interface PrecargaBannerProps {
  jobId: string;
  onComplete: () => void;
}

function PrecargaBanner({ jobId, onComplete }: PrecargaBannerProps) {
  const [status, setStatus] = useState<JobStatus>('queued');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [jobResult, setJobResult] = useState<{ estado?: string; romset?: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const job = await getJob<{ estado?: string; romset?: string }>(jobId);
        if (cancelled) return;
        setStatus(job.status);
        setProgress(job.progress);
        if (job.status === 'succeeded' || job.status === 'failed' || job.status === 'cancelled') {
          setJobResult(job.result);
          onComplete();
          return;
        }
        setTimeout(poll, 500);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Error consultando progreso');
        }
      }
    };
    poll();
    return () => { cancelled = true; };
  }, [jobId, onComplete]);

  const failed = status === 'failed' || (status === 'succeeded' && jobResult && 'error' in jobResult);
  const notFound = status === 'succeeded' && jobResult?.estado === 'no-encontrado';
  const noRomset = status === 'succeeded' && jobResult?.estado === 'sin-romset';
  const systemUnsupported = status === 'succeeded' && jobResult?.estado === 'sistema-no-soportado';
  const isActive = status === 'queued' || status === 'running';

  if (!isActive && !failed) {
    if (notFound || noRomset || systemUnsupported) {
      const reason = notFound
        ? `Romset "${jobResult?.romset}" no encontrado en ArcadeDB.`
        : noRomset
          ? 'El juego no tiene romset definido.'
          : 'El sistema no es compatible con ArcadeDB.';
      return (
        <Panel>
          <SectionHeader>PRECARGA DE ARCADEDB</SectionHeader>
          <SunkenBox className={styles.stack}>
            <p className={styles.meta}>{reason}</p>
          </SunkenBox>
        </Panel>
      );
    }
    return null;
  }

  return (
    <Panel>
      <SectionHeader>PRECARGA DE ARCADEDB</SectionHeader>
      <SunkenBox className={styles.stack}>
        <div className={styles.fieldTop}>
          <span className={styles.name}>
            {failed ? 'Error en la precarga' : 'Buscando datos en ArcadeDB…'}
          </span>
          <span className={styles.meta}>{progress}%</span>
        </div>
        <ProgressBar value={progress} />
        {error ? <p className={styles.error}>{error}</p> : null}
        {failed ? (
          <p className={styles.error}>La precarga falló. Podés reintentar desde la ficha del juego.</p>
        ) : null}
      </SunkenBox>
    </Panel>
  );
}

function CabinetSection({ game }: { game: Game }) {
  const cabinet = game.cabinet;
  const hasData = cabinet?.resolution || cabinet?.orientation || cabinet?.controls;

  return (
    <Panel>
      <SectionHeader>GABINETE</SectionHeader>
      <SunkenBox className={styles.stack}>
        {hasData ? (
          <>
            <div className={styles.fieldTop}>
              <span className={styles.name}>Especificaciones</span>
            </div>
            <div className={styles.cheatLedger}>
              {cabinet?.resolution ? (
                <div className={styles.cheatEntry}>
                  <span>Resolución</span>
                  <span className={styles.meta}>{cabinet.resolution}</span>
                </div>
              ) : null}
              {cabinet?.orientation ? (
                <div className={styles.cheatEntry}>
                  <span>Orientación</span>
                  <span className={styles.meta}>{cabinet.orientation}</span>
                </div>
              ) : null}
              {cabinet?.controls ? (
                <div className={styles.cheatEntry}>
                  <span>Controles</span>
                  <span className={styles.meta}>{cabinet.controls}</span>
                </div>
              ) : null}
              {cabinet?.buttons ? (
                <div className={styles.cheatEntry}>
                  <span>Botones</span>
                  <span className={styles.meta}>{cabinet.buttons}</span>
                </div>
              ) : null}
            </div>
            {cabinet?.button_list.length ? (
              <>
                <div className={styles.fieldTop}>
                  <span className={styles.name}>Mapa de botones</span>
                </div>
                <div className={styles.cheatLedger}>
                  {cabinet.button_list.map((btn, idx) => (
                    <div className={styles.cheatEntry} key={`${btn.control}-${idx}`}>
                      <span>{btn.action}</span>
                      <code>{btn.control}</code>
                      <span className={styles.meta}>{btn.color}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : null}
          </>
        ) : (
          <p className={styles.empty}>Sin Información</p>
        )}
        <p className={styles.meta}>
          Fuente: Arcade Database (motoschifo) — adb.arcadeitalia.net · Historia (C) arcade-history.com
        </p>
      </SunkenBox>
    </Panel>
  );
}
