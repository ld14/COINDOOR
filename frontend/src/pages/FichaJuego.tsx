import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  DosButton,
  DosInput,
  DosTextarea,
  FieldTag,
  Panel,
  ProgressBar,
  SectionHeader,
  StatusBadge,
  SunkenBox,
} from '@/components/dos';
import { SuggestionsModal } from '@/components/SuggestionsModal';
import { useGame } from '@/hooks/useGame';
import { useGameMutations } from '@/hooks/useGameMutations';
import { computeGameStatus, missingRequired } from '@/lib/domain/completeness';
import { FIELDDEFS } from '@/lib/domain/types';
import type {
  CheatGroup,
  Game,
  Identity,
  ImageKey,
  MediaField,
  ReviewCat,
  TextKey,
  VideoKey,
} from '@/lib/domain/types';
import styles from './ReadPages.module.css';

const MANUAL_DELETE_CONFIRM = 'Este campo fue cargado a mano. ¿Borrarlo de todas formas?';

function confirmManualDelete(status: string, action: () => void) {
  if (status === 'manual' && !window.confirm(MANUAL_DELETE_CONFIRM)) return;
  action();
}

const SUGGESTABLE_LABELS: Record<string, string> = {
  sinopsis: 'Sinopsis',
  review: 'Reseña',
  cheats: 'Trucos',
  video: 'Video de gameplay',
};

function suggestionStatus(game: Game, key: string): { hasContent: boolean; isManual: boolean } {
  if (key === 'sinopsis') return { hasContent: game.texts.sinopsis.value !== '', isManual: game.texts.sinopsis.status === 'manual' };
  if (key === 'review') return { hasContent: game.review.status !== 'empty', isManual: game.review.status === 'manual' };
  if (key === 'cheats') return { hasContent: game.cheats.status !== 'empty', isManual: game.cheats.status === 'manual' };
  return { hasContent: game.video.video.status !== 'empty', isManual: game.video.video.status === 'manual' };
}

export function FichaJuego() {
  const { gameId = '' } = useParams();
  const { data: game, error, isLoading } = useGame(gameId);
  const mutations = useGameMutations(gameId);
  const [missingAfterReady, setMissingAfterReady] = useState<string[]>([]);
  const [suggestField, setSuggestField] = useState<string | null>(null);

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
        <IdentitySection game={game} onSave={(identity) => mutations.patchGame.mutate({ identity })} />
        <MediaSection
          game={game}
          onDelete={(key) => mutations.deleteField.mutate(key)}
          onSuggestVideo={() => setSuggestField('video')}
          onUpload={(key, file) => mutations.uploadMedia.mutate({ key, file })}
        />
        <TextSection
          game={game}
          onDelete={(key) => mutations.deleteField.mutate(key)}
          onSuggest={() => setSuggestField('sinopsis')}
          onText={(key, value) => mutations.setTextField.mutate({ key, value })}
        />
        <ReviewSection
          game={game}
          onReview={(score, cats) => mutations.setReview.mutate({ score, cats })}
          onSuggest={() => setSuggestField('review')}
        />
        <CheatsSection
          game={game}
          onCheats={(groups) => mutations.setCheats.mutate({ groups })}
          onSuggest={() => setSuggestField('cheats')}
        />
        <PresentationSection
          game={game}
          onSave={(accentValue, accent2Value) => mutations.patchGame.mutate({
            accent: accentValue ? 'manual' : 'empty',
            accentValue,
            accent2Value,
          })}
        />
        <ManualSection game={game} />
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
    </div>
  );
}

function GameHero({ game, missing, onMarkReady, status }: { game: Game; missing: string[]; onMarkReady: () => void; status: ReturnType<typeof computeGameStatus> }) {
  const heroMedia = game.images.caratula?.url ?? game.video.video?.url;
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
        <DosButton onClick={onMarkReady} variant="primary-small">Marcar como listo</DosButton>
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

function IdentitySection({ game, onSave }: { game: Game; onSave: (identity: Identity) => void }) {
  const [identity, setIdentity] = useState(game.identity);
  useEffect(() => setIdentity(game.identity), [game.identity]);
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
          </label>
        ))}
      </SunkenBox>
      <div className={styles.toolbar}>
        <DosButton onClick={() => onSave(identity)} variant="primary-small">Guardar identidad</DosButton>
      </div>
    </Panel>
  );
}

function MediaSection({
  game,
  onDelete,
  onSuggestVideo,
  onUpload,
}: {
  game: Game;
  onDelete: (key: ImageKey | VideoKey) => void;
  onSuggestVideo: () => void;
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
  const status = field?.status ?? 'empty';
  return (
    <Panel className={styles.stack}>
      <div className={styles.fieldTop}>
        <span className={styles.name}>{label}</span>
        <FieldTag status={status} />
      </div>
      <div className={styles.preview}>
        {field?.url ? <img alt={label} className={styles.previewImage} src={field.url} /> : `${label.toLowerCase()} · ${ratio} · No Disponible`}
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
    </Panel>
  );
}

function TextSection({
  game,
  onDelete,
  onSuggest,
  onText,
}: {
  game: Game;
  onDelete: (key: string) => void;
  onSuggest: () => void;
  onText: (key: TextKey, value: string) => void;
}) {
  const [sinopsis, setSinopsis] = useState(game.texts.sinopsis.value);
  useEffect(() => setSinopsis(game.texts.sinopsis.value), [game.texts.sinopsis.value]);

  return (
    <Panel>
      <SectionHeader>TEXTOS</SectionHeader>
      <SunkenBox>
        <div className={styles.fieldTop}><span className={styles.name}>Sinopsis</span><FieldTag status={game.texts.sinopsis.status} /></div>
        <DosTextarea aria-label="Sinopsis" onChange={(event) => setSinopsis(event.target.value)} value={sinopsis} />
        <div className={styles.toolbar}>
          <DosButton onClick={() => onText('sinopsis', sinopsis)} variant="primary-small">Guardar sinopsis</DosButton>
          <DosButton onClick={onSuggest} variant="ghost-small">Sugerir</DosButton>
          <DosButton onClick={() => confirmManualDelete(game.texts.sinopsis.status, () => onDelete('sinopsis'))} variant="danger-small">Borrar</DosButton>
        </div>
      </SunkenBox>
    </Panel>
  );
}

function ReviewSection({ game, onReview, onSuggest }: { game: Game; onReview: (score: number | null, cats: Partial<Record<ReviewCat, number>>) => void; onSuggest: () => void }) {
  const [reviewScore, setReviewScore] = useState(String(game.review.score ?? ''));
  useEffect(() => setReviewScore(String(game.review.score ?? '')), [game.review.score]);
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
}

function CheatsSection({ game, onCheats, onSuggest }: { game: Game; onCheats: (groups: CheatGroup[]) => void; onSuggest: () => void }) {
  const [cheatName, setCheatName] = useState(game.cheats.groups[0]?.entries[0]?.name ?? '');
  const [cheatInput, setCheatInput] = useState(game.cheats.groups[0]?.entries[0]?.input ?? '');
  useEffect(() => {
    setCheatName(game.cheats.groups[0]?.entries[0]?.name ?? '');
    setCheatInput(game.cheats.groups[0]?.entries[0]?.input ?? '');
  }, [game.cheats.groups]);

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
        <DosInput aria-label="Nombre del truco" onChange={(event) => setCheatName(event.target.value)} value={cheatName} />
        <DosInput aria-label="Input del truco" onChange={(event) => setCheatInput(event.target.value)} value={cheatInput} />
        <div className={styles.toolbar}>
          <DosButton onClick={() => onCheats([{ name: 'general', entries: [{ name: cheatName, input: cheatInput }] }])} variant="primary-small">Guardar trucos</DosButton>
          <DosButton onClick={onSuggest} variant="ghost-small">Sugerir</DosButton>
        </div>
      </SunkenBox>
    </Panel>
  );
}

const hex = (value: string) => `#${value}`;

const ACCENT_PRESETS = [
  { label: 'dorado', value: hex('d4a017'), className: styles.swatchGold },
  { label: 'cian', value: hex('00aaaa'), className: styles.swatchCyan },
  { label: 'rojo', value: hex('aa0000'), className: styles.swatchRed },
  { label: 'verde', value: hex('006600'), className: styles.swatchGreen },
  { label: 'azul', value: hex('0000aa'), className: styles.swatchBlue },
];

function PresentationSection({
  game,
  onSave,
}: {
  game: Game;
  onSave: (accentValue: string, accent2Value: string) => void;
}) {
  const [accentValue, setAccentValue] = useState(game.accentValue);
  const [accent2Value, setAccent2Value] = useState(game.accent2Value);
  useEffect(() => setAccentValue(game.accentValue), [game.accentValue]);
  useEffect(() => setAccent2Value(game.accent2Value), [game.accent2Value]);
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
}

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

function ManualSection({ game }: { game: Game }) {
  return (
    <Panel>
      <SectionHeader>MANUAL</SectionHeader>
      <SunkenBox>
        {game.manuals.length === 0 ? <p>No Disponible</p> : game.manuals.map((manual) => (
          <p key={manual.id}>📎 {manual.fileName} — {manual.status} — {manual.pages} páginas</p>
        ))}
      </SunkenBox>
    </Panel>
  );
}

function MagazineSection({ game }: { game: Game }) {
  return (
    <Panel>
      <SectionHeader>REVISTA</SectionHeader>
      <SunkenBox><p>{game.magazine === 'linked' ? game.magazineName : 'Sin cobertura en revistas'}</p></SunkenBox>
    </Panel>
  );
}

function summary(game: Game, missing: string[]) {
  if (game.errors.length) return `${game.errors.length} error(es) de formato`;
  if (missing.length) return `${missing.length} campo(s) faltante(s)`;
  return 'Completo';
}
