import { useEffect, useMemo, useRef, useState } from 'react';
import { useIsMutating, useQueryClient, type QueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { Card } from '@/components/dos';
import { SuggestionsModal } from '@/components/SuggestionsModal';
import { IdentityBatchModal } from '@/components/IdentityBatchModal';
import { useAutosave, useCongeladoMientrasEdita } from '@/hooks/useAutosave';
import { useFichaProgress, type PendienteFicha } from '@/hooks/useFichaProgress';
import { useGame } from '@/hooks/useGame';
import { invalidarListas, useGameMutations } from '@/hooks/useGameMutations';
import { saveStatusStore } from '@/hooks/useSaveStatus';
import { useSuggestionsJob } from '@/hooks/useSuggestionsJob';
import { useSystems } from '@/hooks/useSystems';
import { soportaArcadeDb, soportaMsdos } from '@/lib/domain/arcade';
import { computeGameStatus, missingRequired } from '@/lib/domain/completeness';
import type { Game, ImageKey } from '@/lib/domain/types';
import { startPrecarga, startPrecargaMsdos } from '@/lib/api/games';
import { ArchivoPanel } from './ficha/ArchivoPanel';
import { CabinetSection } from './ficha/GabineteSection';
import { CheatsSection } from './ficha/TrucosSection';
import { FichaPage, type FichaSeccion } from './ficha/FichaPage';
import { GuiaChecklist } from './ficha/ComoSeJuegaSection';
import { IdentitySection } from './ficha/IdentidadSection';
import { MagazineSection } from './ficha/RevistasSection';
import { ManualSection } from './ficha/ManualSection';
import { GaleriaSection } from './ficha/GaleriaSection';
import { ImagenesSection } from './ficha/ImagenesSection';
import { VideoSection } from './ficha/VideoSection';
import { PrecargaBanner, PrecargaResumen } from './ficha/PrecargaBanner';
import { PrecargaCard } from './ficha/PrecargaCard';
import { PresentationSection } from './ficha/PresentacionSection';
import { ReviewSection } from './ficha/ResenaSection';
import { TextSection } from './ficha/TextosSection';
import { GuiaSection } from './ficha/GuiaSection';
import { SUGGESTABLE_LABELS, suggestionStatus } from './ficha/helpers';
import { irAPendiente } from './ficha/navegacion';
import { resumenPrecarga } from './ficha/precarga';
import type { AccentSlot, PresentationHandle, SaveHandle } from './ficha/types';
import styles from './ficha/ficha.module.css';

// Re-export: los tests y otros módulos importan GuiaChecklist desde acá.
export { GuiaChecklist };

/** Resuelve cuando no queda ninguna mutación en vuelo. */
function esperarMutaciones(queryClient: QueryClient): Promise<void> {
  if (queryClient.isMutating() === 0) return Promise.resolve();
  return new Promise((resolve) => {
    const cancelar = queryClient.getMutationCache().subscribe(() => {
      if (queryClient.isMutating() === 0) {
        cancelar();
        resolve();
      }
    });
  });
}

export function FichaJuego() {
  const { gameId = '' } = useParams();
  const { data: game, error, isLoading, refetch } = useGame(gameId);

  if (isLoading) return <p className={styles.meta}>Cargando ficha…</p>;
  if (error || !game) {
    return (
      <div className={styles.ficha}>
        <Link className={styles.volver} to="/juegos">&lt;&lt; Juegos</Link>
        <Card band="var(--error)" title="Error">
          <p className={styles.error}>Juego no encontrado.</p>
        </Card>
      </div>
    );
  }
  return <FichaContenido game={game} key={game.id} refetchGame={() => void refetch()} />;
}

/**
 * Orquestador de la ficha: carga las mutaciones, cablea el autosave a las secciones y arma la lista
 * de secciones para `FichaPage`. El contrato de las secciones está documentado en `ficha/FichaPage.tsx`.
 */
function FichaContenido({ game: gameVivo, refetchGame }: { game: Game; refetchGame: () => void }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const precargaJobId = searchParams.get('precarga');
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const mutations = useGameMutations(gameVivo.id);
  const { data: systems = [] } = useSystems();
  const [missingAfterReady, setMissingAfterReady] = useState<string[]>([]);
  const [suggestField, setSuggestField] = useState<string | null>(null);
  // Por qué una sugerencia de IA no produjo nada, para mostrarlo en el checklist de la guía.
  const [fallosIA, setFallosIA] = useState<Record<string, string>>({});
  const [suggestIdentityBatch, setSuggestIdentityBatch] = useState(false);
  const [precargaLoading, setPrecargaLoading] = useState(false);
  const [aceptando, setAceptando] = useState(false);
  const [proximoAcento, setProximoAcento] = useState<AccentSlot>(0);
  const manejadores = useRef<Record<string, SaveHandle | null>>({});
  const presentationRef = useRef<PresentationHandle | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const revision = useRef(0);

  const escribiendo = useIsMutating() > 0;
  // El formulario no se recarga bajo los dedos: con un campo con foco o un guardado en vuelo
  // las secciones siguen viendo el último dato previo; el Hero y el progreso usan siempre el vivo.
  const game = useCongeladoMientrasEdita(gameVivo, containerRef, escribiendo);

  const progress = useFichaProgress(gameVivo);
  const missing = missingRequired(gameVivo);
  const status = computeGameStatus(gameVivo);
  const isArcade = soportaArcadeDb(gameVivo.systemId);
  const isMsdos = soportaMsdos(gameVivo.systemId);

  // Candidatas de un slot de imagen: la sección no llama a la API, las busca el orquestador. La búsqueda
  // sale a la red, así que corre SOLO a pedido (clic en ↻ o «Cambiar»), nunca al abrir la ficha
  // (tech-stack §Convenciones, ADR-0015). Si falla, la fila no aparece y queda el modal.
  const [candidatasPedidas, setCandidatasPedidas] = useState<ImageKey | null>(null);
  const candidatasJob = useSuggestionsJob(gameVivo.id, candidatasPedidas ?? '', candidatasPedidas !== null);
  const candidatasImagen = candidatasPedidas && candidatasJob.phase === 'resultados' && candidatasJob.result
    ? { key: candidatasPedidas, candidatos: candidatasJob.result.candidatos.filter((c) => c.key === candidatasPedidas) } // evita candidatas de otro slot en el render previo al reinicio del job
    : null;
  const numeroDe = (clave: string) => progress.secciones.find((s) => s.clave === clave)?.numero;

  const autosave = useAutosave({
    containerRef,
    save: (secciones) => {
      for (const clave of secciones) manejadores.current[clave]?.save();
    },
    waitIdle: () => esperarMutaciones(queryClient),
    isSaving: () => queryClient.isMutating() > 0,
  });

  // Al salir de la ficha se refrescan los listados que se difirieron mientras se editaba.
  useEffect(() => () => { void invalidarListas(queryClient); }, [queryClient]);

  const registrar = (clave: string) => (handle: SaveHandle | null) => { manejadores.current[clave] = handle; };

  /** Guarda lo pendiente y espera; `false` si el guardado falló (no hay que navegar). */
  const guardarYEsperar = async (): Promise<boolean> => {
    await autosave.flushAndWait();
    return saveStatusStore.getSnapshot().kind !== 'error';
  };

  const guardarYSalir = async () => {
    if (await guardarYEsperar()) navigate('/juegos');
  };
  const exportar = async () => {
    if (await guardarYEsperar()) navigate(`/exportar/${gameVivo.id}`);
  };

  // Cada clic en un color predominante alterna: primero el acento primario, después el secundario.
  // Queda cargado en Presentación y se guarda solo, como el resto.
  const aplicarColorDominante = (hex: string) => {
    presentationRef.current?.setAccent(proximoAcento, hex);
    setProximoAcento((slot) => (slot === 0 ? 1 : 0));
  };

  const handlePrecarga = async () => {
    setPrecargaLoading(true);
    try {
      const result = isMsdos
        ? await startPrecargaMsdos(gameVivo.id)
        : await startPrecarga(gameVivo.id);
      setSearchParams({ precarga: result.jobId });
    } catch {
      // Error silenciado: el usuario puede reintentar.
    } finally {
      setPrecargaLoading(false);
    }
  };

  const aceptarUna = async (clave: string) => {
    await autosave.flushAndWait();
    if (clave === 'accent') {
      // El color de acento no tiene endpoint de "aceptar": se confirma con el mismo PATCH que usa Presentación.
      await mutations.patchGame.mutateAsync({ accent: 'manual', accentValue: gameVivo.accentValue, accent2Value: gameVivo.accent2Value });
    } else {
      await mutations.acceptField.mutateAsync(clave);
    }
  };

  const aceptarTodo = async () => {
    setAceptando(true);
    try {
      await autosave.flushAndWait();
      // De a una: cada aceptación reescribe el game.json del juego.
      for (const pendiente of progress.sugerencias) {
        if (pendiente.aceptarClave) await aceptarUna(pendiente.aceptarClave);
      }
    } catch {
      // El error queda en el indicador de la TopBar; las que faltan siguen como sugeridas.
    } finally {
      setAceptando(false);
    }
  };

  /**
   * Recorre las sugerencias: lleva a la próxima y abre el modal de candidatas si el campo lo admite.
   * "Revisar una por una" y "Aceptar todo" salen de `progress.sugerencias`, así que cubren imágenes, video,
   * textos, cómo se juega, trucos, acento y reseña. Identidad queda fuera: sus campos no tienen estado
   * `suggested` (se resuelven con el lote de identidad); Galería tampoco.
   */
  const revisarUnaPorUna = () => {
    const lista = progress.sugerencias;
    if (lista.length === 0) return;
    const pendiente: PendienteFicha = lista[revision.current % lista.length];
    revision.current += 1;
    if (containerRef.current) irAPendiente(containerRef.current, pendiente, false);
    if (pendiente.aceptarClave && SUGGESTABLE_LABELS[pendiente.aceptarClave]) setSuggestField(pendiente.aceptarClave);
  };

  const resumen = useMemo(() => resumenPrecarga(gameVivo), [gameVivo]);
  const fuente = resumen.fuentes.length === 1
    ? resumen.fuentes[0]
    : isArcade ? 'ArcadeDB' : isMsdos ? 'Launchbox + IA' : 'Las fuentes';

  const banner = precargaJobId ? (
    <PrecargaBanner
      jobId={precargaJobId}
      onComplete={() => {
        setSearchParams({});
        refetchGame();
      }}
    />
  ) : (
    <PrecargaResumen
      aceptando={aceptando}
      fuente={fuente}
      onAcceptAll={() => void aceptarTodo()}
      onReviewOneByOne={revisarUnaPorUna}
      resumen={resumen}
    />
  );

  const avisos = (
    <>
      {mutations.patchGame.error ? (
        <Card band="var(--error)" title="NO SE GUARDÓ EL CAMBIO:">
          <p className={styles.error}>{mutations.patchGame.error.message}</p>
        </Card>
      ) : null}

      {missingAfterReady.length > 0 ? (
        <Card band="var(--error)" title="NO SE PUEDE MARCAR COMO LISTO — faltan campos requeridos:">
          {missingAfterReady.map((item) => <p className={styles.error} key={item}>- {item}</p>)}
        </Card>
      ) : null}

      {gameVivo.errors.length > 0 ? (
        <Card band="var(--error)" title="ERRORES DE FORMATO (bloquean el export):">
          {gameVivo.errors.map((item) => (
            <p className={styles.error} key={`${item.field}-${item.message}`}>
              - {item.field} — {item.message}
            </p>
          ))}
        </Card>
      ) : null}
    </>
  );

  const secciones: FichaSeccion[] = [
    {
      clave: 'identidad',
      node: <IdentitySection ref={registrar('identidad')} game={game} onSave={(identity) => mutations.patchGame.mutate({ identity })} onSuggest={setSuggestField} onSuggestBatch={() => setSuggestIdentityBatch(true)} />,
    },
    {
      clave: 'presentacion',
      soloAlSalir: true, // un hex a medio escribir no es un color válido
      node: (
        <PresentationSection
          ref={(handle) => { manejadores.current.presentacion = handle; presentationRef.current = handle; }}
          game={game}
          onSave={(accentValue, accent2Value) => mutations.patchGame.mutate({
            accent: accentValue ? 'manual' : 'empty',
            accentValue,
            accent2Value,
          })}
        />
      ),
    },
    {
      clave: 'imagenes',
      node: (
        <ImagenesSection
          candidatas={candidatasImagen}
          game={game}
          onDelete={(key) => mutations.deleteField.mutate(key)}
          onPickCandidata={(key, candidateId) => mutations.applySuggestion.mutate({ key, candidateId })}
          onSuggestImage={(key) => { setCandidatasPedidas(key); setSuggestField(key); }}
          onUpload={(key, file) => mutations.uploadMedia.mutate({ key, file })}
        />
      ),
    },
    {
      clave: 'galeria',
      // TODO(backend): tilde «va en el paquete» por miniatura; requiere cambiar el contrato de la galería (ADR).
      node: <GaleriaSection game={game} numero={numeroDe('galeria')} onChanged={refetchGame} />,
    },
    {
      clave: 'video',
      node: (
        <VideoSection
          game={game}
          onDelete={(key) => mutations.deleteField.mutate(key)}
          onSuggestVideo={() => setSuggestField('video')}
          onUpload={(key, file) => mutations.uploadMedia.mutate({ key, file })}
        />
      ),
    },
    {
      clave: 'textos',
      node: (
        <TextSection
          ref={registrar('textos')}
          game={game}
          onDelete={(key) => mutations.deleteField.mutate(key)}
          onSuggest={setSuggestField}
          onText={(key, value) => mutations.setTextField.mutate({ key, value })}
        />
      ),
    },
    {
      clave: 'resena',
      node: (
        <ReviewSection
          ref={registrar('resena')}
          game={game}
          numero={numeroDe('resena')}
          onReview={(score, cats) => mutations.setReview.mutate({ score, cats })}
          onSuggest={() => setSuggestField('review')}
        />
      ),
    },
    {
      clave: 'guia',
      node: (
        <GuiaSection
          ref={registrar('guia')}
          game={game}
          onDelete={(key) => mutations.deleteField.mutate(key)}
          onSuggest={setSuggestField}
          onText={(key, value) => mutations.setTextField.mutate({ key, value })}
          onButtons={(cabinetButtons) => mutations.patchGame.mutate({ cabinetButtons })}
        />
      ),
    },
    {
      clave: 'trucos',
      node: (
        // TODO(backend): casilla «va en el paquete» por truco; requiere un campo nuevo en el modelo (ADR).
        <CheatsSection
          ref={registrar('trucos')}
          game={game}
          numero={numeroDe('trucos')}
          onCheats={(groups) => mutations.setCheats.mutate({ groups })}
          onDelete={() => mutations.deleteField.mutate('cheats')}
          onSuggest={() => setSuggestField('cheats')}
        />
      ),
    },
    {
      clave: 'manual',
      node: (
        <>
          <ManualSection game={game} onUpload={(file) => mutations.uploadManual.mutate(file)} onUploadAsync={(file) => mutations.uploadManual.mutateAsync(file)} onDelete={(id) => mutations.deleteManual.mutate(id)} />
          <MagazineSection game={game} />
        </>
      ),
    },
  ];

  const lateral: FichaSeccion[] = [
    {
      clave: 'archivo',
      node: (
        <ArchivoPanel
          ref={registrar('archivo')}
          game={game}
          onSaveRomRef={(romRef) => mutations.patchGame.mutate({ romRef })}
          onSaveTratamiento={(tratamiento) => mutations.patchGame.mutate({ tratamiento })}
          onUploadRom={(file) => mutations.uploadRom.mutate(file)}
        />
      ),
    },
    { clave: 'guia-checklist', node: <GuiaChecklist items={game.guiaChecklist ?? []} fallos={fallosIA} /> },
    { clave: 'gabinete', node: <CabinetSection game={game} /> },
    {
      clave: 'precarga',
      node: (isArcade || isMsdos) && !precargaJobId
        ? <PrecargaCard cargando={precargaLoading} onPrecargar={() => void handlePrecarga()} tipo={isMsdos ? 'msdos' : 'arcade'} />
        : null,
    },
  ];

  return (
    <>
      <FichaPage
        autosave={autosave}
        avisos={avisos}
        banner={banner}
        containerRef={containerRef}
        game={gameVivo}
        lateral={lateral}
        onAcceptKey={(clave) => void aceptarUna(clave).catch(() => undefined)}
        onExport={() => void exportar()}
        onMarkReady={() => {
          setMissingAfterReady(missing);
          if (missing.length === 0) void mutations.markReady.mutateAsync().catch(() => undefined);
        }}
        onPickColor={aplicarColorDominante}
        onSaveDraft={() => void guardarYSalir()}
        onSystemChange={(systemId) => mutations.patchGame.mutate({ systemId })}
        progress={progress}
        proximoAcento={proximoAcento}
        secciones={secciones}
        status={status}
        systems={systems}
      />

      {suggestField ? (
        <SuggestionsModal
          fieldKey={suggestField}
          gameId={gameVivo.id}
          hasContent={suggestionStatus(game, suggestField).hasContent}
          isManual={suggestionStatus(game, suggestField).isManual}
          label={SUGGESTABLE_LABELS[suggestField]}
          onApply={(candidateId) => mutations.applySuggestion.mutate({ key: suggestField, candidateId })}
          onClose={() => setSuggestField(null)}
          onOutcome={(key, motivo) => setFallosIA((prev) => {
            const resto = { ...prev };
            delete resto[key];
            return motivo ? { ...resto, [key]: motivo } : resto;
          })}
          open
          current={{ previewUrl: suggestionStatus(game, suggestField).previewUrl, value: suggestionStatus(game, suggestField).value }}
        />
      ) : null}

      {suggestIdentityBatch ? (
        <IdentityBatchModal
          gameId={gameVivo.id}
          open={suggestIdentityBatch}
          onClose={() => setSuggestIdentityBatch(false)}
          onApplied={refetchGame}
        />
      ) : null}
    </>
  );
}
