import { useRef, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { DosButton, Panel, SectionHeader, SunkenBox } from '@/components/dos';
import { SuggestionsModal } from '@/components/SuggestionsModal';
import { IdentityBatchModal } from '@/components/IdentityBatchModal';
import { useGame } from '@/hooks/useGame';
import { useGameMutations } from '@/hooks/useGameMutations';
import { useSystems } from '@/hooks/useSystems';
import { soportaArcadeDb, soportaMsdos } from '@/lib/domain/arcade';
import { computeGameStatus, missingRequired } from '@/lib/domain/completeness';
import { startPrecarga, startPrecargaMsdos } from '@/lib/api/games';
import { CabinetSection } from './ficha/GabineteSection';
import { CheatsSection } from './ficha/TrucosSection';
import { CompletionDashboard } from './ficha/CompletionDashboard';
import { GameHero } from './ficha/GameHero';
import { GuiaChecklist } from './ficha/ComoSeJuegaSection';
import { IdentitySection } from './ficha/IdentidadSection';
import { MagazineSection } from './ficha/RevistasSection';
import { ManualSection } from './ficha/ManualSection';
import { MediaSection } from './ficha/ImagenesSection';
import { PrecargaBanner } from './ficha/PrecargaBanner';
import { PresentationSection } from './ficha/PresentacionSection';
import { ReviewSection } from './ficha/ResenaSection';
import { TextSection } from './ficha/TextosSection';
import { SUGGESTABLE_LABELS, suggestionStatus } from './ficha/helpers';
import type { AccentSlot, PresentationHandle, SaveHandle } from './ficha/types';
import styles from './ReadPages.module.css';

// Re-export: los tests y otros módulos importan GuiaChecklist desde acá.
export { GuiaChecklist };

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
  // Por qué una sugerencia de IA no produjo nada, para mostrarlo en el checklist de la guía.
  const [fallosIA, setFallosIA] = useState<Record<string, string>>({});
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
          onSuggest={setSuggestField}
          onText={(key, value) => mutations.setTextField.mutate({ key, value })}
        />
        <GuiaChecklist items={game.guiaChecklist ?? []} fallos={fallosIA} />
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
          onOutcome={(key, motivo) => setFallosIA((prev) => {
            const { [key]: _anterior, ...resto } = prev;
            return motivo ? { ...resto, [key]: motivo } : resto;
          })}
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
