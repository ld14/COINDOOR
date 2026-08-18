import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createGame, markReady, patchGame, uploadRom, type CreateGamePayload } from '@/lib/api/games';
import { deleteField, setCheats, setReview, setTextField } from '@/lib/api/fields';
import { deleteManual, uploadManual } from '@/lib/api/manuals';
import { uploadMedia } from '@/lib/api/media';
import { applySuggestion } from '@/lib/api/suggestions';
import type { CheatsField, Game, ImageKey, ReviewField, TextKey, VideoKey } from '@/lib/domain/types';

export function useGameMutations(gameId?: string) {
  const queryClient = useQueryClient();
  const invalidate = async (game?: Game) => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['games'] }),
      queryClient.invalidateQueries({ queryKey: ['systems'] }),
      queryClient.invalidateQueries({ queryKey: ['game', game?.id ?? gameId] }),
    ]);
  };

  return {
    createGame: useMutation({ mutationFn: (payload: CreateGamePayload) => createGame(payload), onSuccess: invalidate }),
    patchGame: useMutation({ mutationFn: (payload: Parameters<typeof patchGame>[1]) => patchGame(gameId ?? '', payload), onSuccess: invalidate }),
    markReady: useMutation({ mutationFn: () => markReady(gameId ?? ''), onSuccess: invalidate }),
    setTextField: useMutation({ mutationFn: ({ key, value }: { key: TextKey; value: string }) => setTextField(gameId ?? '', key, value), onSuccess: invalidate }),
    deleteField: useMutation({ mutationFn: (key: string) => deleteField(gameId ?? '', key), onSuccess: invalidate }),
    setReview: useMutation({ mutationFn: (review: Pick<ReviewField, 'score' | 'cats'>) => setReview(gameId ?? '', review), onSuccess: invalidate }),
    setCheats: useMutation({ mutationFn: (cheats: Pick<CheatsField, 'groups'>) => setCheats(gameId ?? '', cheats), onSuccess: invalidate }),
    uploadMedia: useMutation({ mutationFn: ({ key, file }: { key: ImageKey | VideoKey; file: File }) => uploadMedia(gameId ?? '', key, file), onSuccess: invalidate }),
    uploadRom: useMutation({ mutationFn: (file: File) => uploadRom(gameId ?? '', file), onSuccess: invalidate }),
    applySuggestion: useMutation({ mutationFn: ({ key, candidateId }: { key: string; candidateId: string }) => applySuggestion(gameId ?? '', key, candidateId), onSuccess: invalidate }),
    uploadManual: useMutation({ mutationFn: (file: File) => uploadManual(gameId ?? '', file), onSuccess: invalidate }),
    deleteManual: useMutation({ mutationFn: (manualId: string) => deleteManual(gameId ?? '', manualId), onSuccess: invalidate }),
  };
}
