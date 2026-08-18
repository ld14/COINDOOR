import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  DosButton,
  DosInput,
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
import { useGame } from '@/hooks/useGame';
import { useGameMutations } from '@/hooks/useGameMutations';
import { useDominantColors } from '@/hooks/useDominantColors';
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
  TextKey,
  VideoKey,
} from '@/lib/domain/types';
import { searchManuals, type ManualSearchResult } from '@/lib/api/manuals';
import { searchMagazines, setMagazine, addAppearance, removeAppearance, buildMagazineLinks, type MagazineSearchResult } from '@/lib/api/magazines';
import styles from './ReadPages.module.css';

const MANUAL_DELETE_CONFIRM = 'Este campo fue cargado a mano. ¿Borrarlo de todas formas?';

type SaveHandle = { save: () => void };

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

function suggestionStatus(game: Game, key: string): { hasContent: boolean; isManual: boolean } {
  if (isIdentityKey(key)) return { hasContent: game.identity[key] !== '', isManual: game.identitySource === 'manual' };
  if (FIELDDEFS.images.some((f) => f.key === key)) {
    const img = game.images[key as ImageKey];
    return { hasContent: img?.status !== 'empty', isManual: img?.status === 'manual' };
  }
  if (key === 'sinopsis') return { hasContent: game.texts.sinopsis.value !== '', isManual: game.texts.sinopsis.status === 'manual' };
  if (key === 'review') return { hasContent: game.review.status !== 'empty', isManual: game.review.status === 'manual' };
  if (key === 'cheats') return { hasContent: game.cheats.status !== 'empty', isManual: game.cheats.status === 'manual' };
  return { hasContent: game.video.video.status !== 'empty', isManual: game.video.video.status === 'manual' };
}

export function FichaJuego() {
  const { gameId = '' } = useParams();
  const { data: game, error, isLoading, refetch: refetchGame } = useGame(gameId);
  const mutations = useGameMutations(gameId);
  const [missingAfterReady, setMissingAfterReady] = useState<string[]>([]);
  const [suggestField, setSuggestField] = useState<string | null>(null);
  const [suggestIdentityBatch, setSuggestIdentityBatch] = useState(false);
  const sectionRefs = useRef<Record<string, SaveHandle | null>>({});

  const saveAll = () => {
    for (const ref of Object.values(sectionRefs.current)) ref?.save();
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

  const missing = missingRequired(game);
  const status = computeGameStatus(game);

  return (
    <div className={styles.page}>
      <GameHero
        game={game}
        missing={missing}
        onSaveAll={saveAll}
        onMarkReady={() => {
          setMissingAfterReady(missing);
          if (missing.length === 0) void mutations.markReady.mutateAsync();
        }}
        status={status}
      />

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
          onSuggest={() => setSuggestField('cheats')}
        />
        <PresentationSection
          ref={(r) => { sectionRefs.current.presentation = r; }}
          game={game}
          onSave={(accentValue, accent2Value) => mutations.patchGame.mutate({
            accent: accentValue ? 'manual' : 'empty',
            accentValue,
            accent2Value,
          })}
        />
        <ManualSection game={game} onUpload={(file) => mutations.uploadManual.mutate(file)} onDelete={(id) => mutations.deleteManual.mutate(id)} />
        <MagazineSection game={game} />
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

function GameHero({ game, missing, onSaveAll, onMarkReady, status }: { game: Game; missing: string[]; onSaveAll: () => void; onMarkReady: () => void; status: ReturnType<typeof computeGameStatus> }) {
  const coverUrl = game.images.caratula?.url;
  const heroMedia = coverUrl ?? game.video.video?.url;
  const { colors } = useDominantColors(coverUrl, 4);

  return (
    <Panel className={styles.gameHero}>
      <div className={styles.heroPreview}>
        {heroMedia ? <img alt={game.identity.title} className={styles.previewImage} src={heroMedia} /> : `${game.identity.title} · carátula pendiente`}
      </div>
      <div className={styles.heroStatus}>
        <Link className={styles.backLink} to="/juegos">&lt;&lt; Juegos</Link>
        <div>
          <h1 className={styles.title}>{game.identity.title}</h1>
          <p className={styles.meta}>{game.systemId} · {game.identity.year || 'Sin Información'} · {game.identitySource}</p>
        </div>
        <StatusBadge status={status} />
        <p className={styles.meta}>{summary(game, missing)}</p>
        {colors.length > 0 ? (
          <div className={styles.colorPalette}>
            <span className={styles.paletteLabel}>Colores predominantes</span>
            <div className={styles.swatches}>
              {colors.map((color) => (
                <div key={color.hex} className={styles.colorSwatch}>
                  <div className={styles.colorBlock} style={{ backgroundColor: color.hex }} />
                  <span className={styles.colorHex}>{color.hex}</span>
                </div>
              ))}
            </div>
          </div>
        ) : null}
        <div className={styles.toolbar}>
          <DosButton onClick={onSaveAll} variant="primary-small">Guardar todo</DosButton>
          <DosButton onClick={onMarkReady} variant="primary-small">Marcar como listo</DosButton>
        </div>
      </div>
    </Panel>
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
}: {
  game: Game;
  onDelete: (key: ImageKey | VideoKey) => void;
  onSuggestVideo: () => void;
  onSuggestImage: (key: ImageKey) => void;
  onUpload: (key: ImageKey | VideoKey, file: File) => void;
}) {
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
            />
          ))}
        </div>
      </Panel>
    </>
  );
}

function MediaCard({
  field,
  label,
  mediaKey,
  onDelete,
  onSuggest,
  onUpload,
  ratio,
}: {
  field?: MediaField;
  label: string;
  mediaKey: ImageKey | VideoKey;
  onDelete: (key: ImageKey | VideoKey) => void;
  onSuggest?: () => void;
  onUpload: (key: ImageKey | VideoKey, file: File) => void;
  ratio: string;
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
              src={field.url}
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

const CheatsSection = forwardRef<SaveHandle, { game: Game; onCheats: (groups: CheatGroup[]) => void; onSuggest: () => void }>(function CheatsSection({ game, onCheats, onSuggest }, ref) {
  useImperativeHandle(ref, () => ({
    save: () => onCheats(game.cheats.groups),
  }), [onCheats, game.cheats.groups]);

  return (
    <Panel>
      <SectionHeader>TRUCOS</SectionHeader>
      <SunkenBox className={styles.stack}>
        <div className={styles.fieldTop}><span className={styles.name}>Códigos cargados</span><FieldTag status={game.cheats.status} /></div>
        {game.cheats.groups.length > 0 ? (
          <div className={styles.cheatLedger}>
            {game.cheats.groups.map((group) => (
              <div className={styles.cheatGroup} key={group.name}>
                <span className={styles.cheatGroupName}>{group.name}</span>
                {group.entries.map((entry) => (
                  <div className={styles.cheatEntry} key={`${group.name}-${entry.name}-${entry.input}`}>
                    <span>{entry.name}</span>
                    <code>{entry.input}</code>
                  </div>
                ))}
              </div>
            ))}
          </div>
        ) : <p className={styles.empty}>No Disponible</p>}
        <div className={styles.toolbar}>
          <DosButton onClick={onSuggest} variant="ghost-small">Sugerir</DosButton>
        </div>
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

const PresentationSection = forwardRef<SaveHandle, {
  game: Game;
  onSave: (accentValue: string, accent2Value: string) => void;
}>(function PresentationSection({ game, onSave }, ref) {
  const [accentValue, setAccentValue] = useState(game.accentValue);
  const [accent2Value, setAccent2Value] = useState(game.accent2Value);
  useEffect(() => setAccentValue(game.accentValue), [game.accentValue]);
  useEffect(() => setAccent2Value(game.accent2Value), [game.accent2Value]);
  useImperativeHandle(ref, () => ({ save: () => onSave(accentValue, accent2Value) }), [onSave, accentValue, accent2Value]);
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
