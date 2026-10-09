import { useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query';
import { createGame, markReady, patchGame, uploadRom, type CreateGamePayload } from '@/lib/api/games';
import { acceptField, deleteField, setCheats, setReview, setTextField } from '@/lib/api/fields';
import { deleteManual, uploadManual } from '@/lib/api/manuals';
import { uploadMedia } from '@/lib/api/media';
import { applySuggestion } from '@/lib/api/suggestions';
import type { CheatsField, ImageKey, ReviewField, TextKey, VideoKey } from '@/lib/domain/types';
import { saveStatusStore } from './useSaveStatus';

/** Cuánto esperar sin escrituras antes de refrescar los listados (juegos, sistemas, ROMs). */
const LISTAS_DELAY_MS = 2000;
let listasTimer: ReturnType<typeof setTimeout> | null = null;

/**
 * Refresca lo que depende de TODOS los juegos: el listado, los contadores de sistemas y los
 * candidatos de ROM. Mientras se edita una ficha no hace falta (el formulario solo lee
 * `['game', id]`), así que se difiere hasta que cesen las escrituras o se llame a esto al salir.
 */
export function invalidarListas(queryClient: QueryClient): Promise<unknown> {
  if (listasTimer !== null) {
    clearTimeout(listasTimer);
    listasTimer = null;
  }
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: ['games'] }),
    queryClient.invalidateQueries({ queryKey: ['systems'] }),
    queryClient.invalidateQueries({ queryKey: ['rom-candidates'] }),
  ]);
}

function programarListas(queryClient: QueryClient) {
  if (listasTimer !== null) clearTimeout(listasTimer);
  listasTimer = setTimeout(() => {
    listasTimer = null;
    void invalidarListas(queryClient);
  }, LISTAS_DELAY_MS);
}

function idDe(data: unknown): string | undefined {
  if (typeof data === 'object' && data !== null && 'id' in data && typeof data.id === 'string') return data.id;
  return undefined;
}

export function useGameMutations(gameId?: string) {
  const queryClient = useQueryClient();

  // Con `gameId` (la ficha) solo se recarga ese juego y los listados se difieren: así un
  // autosave no dispara tres refetch por cada pausa al escribir. Sin `gameId` (alta de un
  // juego) se invalida todo de inmediato.
  const invalidate = async (data?: unknown) => {
    const id = idDe(data) ?? gameId;
    if (gameId) {
      await queryClient.invalidateQueries({ queryKey: ['game', id] });
      programarListas(queryClient);
      return;
    }
    await Promise.all([
      invalidarListas(queryClient),
      queryClient.invalidateQueries({ queryKey: ['game', id] }),
    ]);
  };

  // Las escrituras alimentan el indicador de guardado de la TopBar. `clave` dice qué dato escriben:
  // un fallo se recuerda por clave, "Reintentar" lo vuelve a mandar y una escritura posterior sobre
  // la misma clave lo reemplaza.
  const guardado = <TVars, TData>(clave: (vars: TVars) => string, mutationFn: (vars: TVars) => Promise<TData>) => {
    const reintentar = (vars: TVars) => {
      saveStatusStore.begin();
      mutationFn(vars).then(
        (data) => {
          saveStatusStore.succeed(clave(vars));
          return invalidate(data);
        },
        (error: Error) => saveStatusStore.fail(error.message, clave(vars), () => reintentar(vars)),
      );
    };
    return {
      mutationFn,
      onMutate: () => saveStatusStore.begin(),
      onSuccess: (data: TData, vars: TVars) => {
        saveStatusStore.succeed(clave(vars));
        return invalidate(data);
      },
      onError: (error: Error, vars: TVars) => saveStatusStore.fail(error.message, clave(vars), () => reintentar(vars)),
    };
  };
  // Acciones cuya falla el usuario ve en su propio lugar (alta de juego, "marcar como listo").
  const accion = <TVars, TData>(mutationFn: (vars: TVars) => Promise<TData>) => ({
    mutationFn,
    onSuccess: (data: TData) => invalidate(data),
  });
  // Todo lo que escribe un campo del juego comparte clave: la última escritura gana.
  const campo = (key: string) => `campo:${key}`;

  return {
    createGame: useMutation(accion((payload: CreateGamePayload) => createGame(payload))),
    patchGame: useMutation(guardado((payload: Parameters<typeof patchGame>[1]) => `juego:${Object.keys(payload).sort().join(',')}`, (payload: Parameters<typeof patchGame>[1]) => patchGame(gameId ?? '', payload))),
    markReady: useMutation(accion(() => markReady(gameId ?? ''))),
    setTextField: useMutation(guardado(({ key }: { key: TextKey; value: string }) => campo(key), ({ key, value }: { key: TextKey; value: string }) => setTextField(gameId ?? '', key, value))),
    deleteField: useMutation(guardado((key: string) => campo(key), (key: string) => deleteField(gameId ?? '', key))),
    setReview: useMutation(guardado(() => campo('review'), (review: Pick<ReviewField, 'score' | 'cats'>) => setReview(gameId ?? '', review))),
    setCheats: useMutation(guardado(() => campo('cheats'), (cheats: Pick<CheatsField, 'groups'>) => setCheats(gameId ?? '', cheats))),
    uploadMedia: useMutation(guardado(({ key }: { key: ImageKey | VideoKey; file: File }) => campo(key), ({ key, file }: { key: ImageKey | VideoKey; file: File }) => uploadMedia(gameId ?? '', key, file))),
    uploadRom: useMutation(guardado(() => 'rom', (file: File) => uploadRom(gameId ?? '', file))),
    applySuggestion: useMutation(guardado(({ key }: { key: string; candidateId: string }) => campo(key), ({ key, candidateId }: { key: string; candidateId: string }) => applySuggestion(gameId ?? '', key, candidateId))),
    /** Pasa un campo `suggested` a `manual` (POST /games/{id}/fields/{key}/accept). */
    acceptField: useMutation(guardado((key: string) => campo(key), (key: string) => acceptField(gameId ?? '', key))),
    uploadManual: useMutation(guardado((file: File) => `manual-subida:${file.name}`, (file: File) => uploadManual(gameId ?? '', file))),
    deleteManual: useMutation(guardado((manualId: string) => `manual-borrar:${manualId}`, (manualId: string) => deleteManual(gameId ?? '', manualId))),
  };
}
